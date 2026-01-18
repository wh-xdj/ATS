#!/bin/bash

# ATS 统一启动脚本
# 用于启动前端、后端、Docker和Agent服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
AGENT_DIR="${PROJECT_ROOT}/agent"
PID_FILE="${PROJECT_ROOT}/.ats_pids"

# 日志文件
LOG_DIR="${PROJECT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 未安装，请先安装"
        return 1
    fi
    return 0
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0
    fi
    return 1
}

# 等待服务就绪
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=0
    
    print_info "等待服务启动: ${url}"
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "${url}" > /dev/null 2>&1; then
            print_success "服务已就绪: ${url}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    print_warning "服务启动超时: ${url}"
    return 1
}

# 启动Docker服务
start_docker() {
    print_info "启动Docker服务..."
    cd "${BACKEND_DIR}"
    
    if ! check_command docker; then
        print_error "Docker 未安装，跳过Docker服务启动"
        return 1
    fi
    
    if ! check_command docker-compose; then
        print_error "docker-compose 未安装，跳过Docker服务启动"
        return 1
    fi
    
    # 检查Docker是否运行
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker守护进程未运行，请先启动Docker"
        return 1
    fi
    
    # 启动docker-compose服务
    docker-compose up -d
    
    print_success "Docker服务已启动"
    print_info "等待Docker服务就绪..."
    sleep 5
    
    # 检查MySQL是否就绪
    local mysql_ready=false
    for i in {1..30}; do
        if docker exec ats-mysql mysqladmin ping -h localhost -u ats_user -pats_password --silent 2>/dev/null; then
            mysql_ready=true
            break
        fi
        sleep 1
    done
    
    if [ "$mysql_ready" = true ]; then
        print_success "MySQL已就绪"
    else
        print_warning "MySQL可能尚未完全就绪，但将继续启动其他服务"
    fi
    
    return 0
}

# 启动后端服务
start_backend() {
    print_info "启动后端服务..."
    cd "${BACKEND_DIR}"
    
    # 检查端口8000是否被占用
    if check_port 8000; then
        print_warning "端口8000已被占用，跳过后端启动"
        return 1
    fi
    
    # 检查是否使用uv
    if command -v uv &> /dev/null; then
        print_info "使用uv启动后端服务..."
        nohup uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload > "${LOG_DIR}/backend.log" 2>&1 &
        BACKEND_PID=$!
    elif [ -d ".venv" ]; then
        print_info "使用虚拟环境启动后端服务..."
        source .venv/bin/activate
        nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > "${LOG_DIR}/backend.log" 2>&1 &
        BACKEND_PID=$!
    else
        print_info "使用系统Python启动后端服务..."
        nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > "${LOG_DIR}/backend.log" 2>&1 &
        BACKEND_PID=$!
    fi
    
    echo "backend:${BACKEND_PID}" >> "${PID_FILE}"
    print_success "后端服务已启动 (PID: ${BACKEND_PID})"
    print_info "后端日志: ${LOG_DIR}/backend.log"
    
    # 等待后端就绪
    wait_for_service "http://localhost:8000/health"
    
    return 0
}

# 启动前端服务
start_frontend() {
    print_info "启动前端服务..."
    cd "${FRONTEND_DIR}"
    
    # 检查端口5173（Vite默认端口）是否被占用
    if check_port 5173; then
        print_warning "端口5173已被占用，跳过前端启动"
        return 1
    fi
    
    # 检查node_modules是否存在
    if [ ! -d "node_modules" ]; then
        print_warning "node_modules不存在，正在安装依赖..."
        if ! check_command npm; then
            print_error "npm 未安装，无法启动前端服务"
            return 1
        fi
        npm install
    fi
    
    # 启动前端服务
    nohup npm run dev > "${LOG_DIR}/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    
    echo "frontend:${FRONTEND_PID}" >> "${PID_FILE}"
    print_success "前端服务已启动 (PID: ${FRONTEND_PID})"
    print_info "前端日志: ${LOG_DIR}/frontend.log"
    
    # 等待前端就绪
    sleep 3
    if check_port 5173; then
        print_success "前端服务已就绪: http://localhost:5173"
    else
        print_warning "前端服务可能尚未完全就绪"
    fi
    
    return 0
}

# 启动Agent服务
start_agent() {
    print_info "启动Agent服务..."
    cd "${AGENT_DIR}"
    
    # 检查环境变量或配置文件
    local token="${AGENT_TOKEN:-}"
    local server_url="${AGENT_SERVER_URL:-ws://localhost:8000/ws/agent}"
    
    if [ -z "$token" ]; then
        # 尝试从配置文件读取
        if [ -f "config.yaml" ]; then
            print_info "从config.yaml读取配置..."
            # 这里可以添加解析yaml的逻辑，但为了简单，我们使用环境变量
        fi
        
        if [ -z "$token" ]; then
            print_warning "未设置AGENT_TOKEN环境变量，Agent将无法连接到服务器"
            print_info "提示: 设置环境变量 AGENT_TOKEN 和 AGENT_SERVER_URL 来启动Agent"
            print_info "例如: export AGENT_TOKEN='your-token' && export AGENT_SERVER_URL='ws://localhost:8000/ws/agent'"
            read -p "是否继续启动Agent? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_info "跳过Agent启动"
                return 0
            fi
        fi
    fi
    
    # 启动Agent
    if command -v uv &> /dev/null; then
        print_info "使用uv启动Agent服务..."
        if [ -n "$token" ]; then
            nohup uv run python agent.py --token "${token}" --server-url "${server_url}" > "${LOG_DIR}/agent.log" 2>&1 &
        else
            nohup uv run python agent.py --server-url "${server_url}" > "${LOG_DIR}/agent.log" 2>&1 &
        fi
        AGENT_PID=$!
    elif [ -d ".venv" ]; then
        print_info "使用虚拟环境启动Agent服务..."
        source .venv/bin/activate
        if [ -n "$token" ]; then
            nohup python agent.py --token "${token}" --server-url "${server_url}" > "${LOG_DIR}/agent.log" 2>&1 &
        else
            nohup python agent.py --server-url "${server_url}" > "${LOG_DIR}/agent.log" 2>&1 &
        fi
        AGENT_PID=$!
    else
        print_info "使用系统Python启动Agent服务..."
        if [ -n "$token" ]; then
            nohup python agent.py --token "${token}" --server-url "${server_url}" > "${LOG_DIR}/agent.log" 2>&1 &
        else
            nohup python agent.py --server-url "${server_url}" > "${LOG_DIR}/agent.log" 2>&1 &
        fi
        AGENT_PID=$!
    fi
    
    echo "agent:${AGENT_PID}" >> "${PID_FILE}"
    print_success "Agent服务已启动 (PID: ${AGENT_PID})"
    print_info "Agent日志: ${LOG_DIR}/agent.log"
    
    return 0
}

# 停止所有服务
stop_all() {
    print_info "停止所有服务..."
    
    # 停止通过PID文件管理的服务
    if [ -f "${PID_FILE}" ]; then
        while IFS=: read -r service pid; do
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                print_info "停止 ${service} 服务 (PID: ${pid})..."
                kill "$pid" 2>/dev/null || true
            fi
        done < "${PID_FILE}"
        rm -f "${PID_FILE}"
    fi
    
    # 停止Docker服务
    if [ -f "${BACKEND_DIR}/docker-compose.yml" ]; then
        cd "${BACKEND_DIR}"
        if command -v docker-compose &> /dev/null; then
            print_info "停止Docker服务..."
            docker-compose down
        fi
    fi
    
    print_success "所有服务已停止"
}

# 显示服务状态
show_status() {
    print_info "服务状态:"
    echo
    
    # Docker服务状态
    if command -v docker-compose &> /dev/null && [ -f "${BACKEND_DIR}/docker-compose.yml" ]; then
        cd "${BACKEND_DIR}"
        echo "Docker服务:"
        docker-compose ps
        echo
    fi
    
    # 其他服务状态
    if [ -f "${PID_FILE}" ]; then
        echo "其他服务:"
        while IFS=: read -r service pid; do
            if [ -n "$pid" ]; then
                if kill -0 "$pid" 2>/dev/null; then
                    echo "  ${service}: 运行中 (PID: ${pid})"
                else
                    echo "  ${service}: 已停止 (PID: ${pid})"
                fi
            fi
        done < "${PID_FILE}"
    fi
    
    # 端口检查
    echo
    echo "端口状态:"
    if check_port 8000; then
        echo "  8000 (后端): 已占用"
    else
        echo "  8000 (后端): 空闲"
    fi
    
    if check_port 5173; then
        echo "  5173 (前端): 已占用"
    else
        echo "  5173 (前端): 空闲"
    fi
}

# 清理函数
cleanup() {
    print_info "接收到中断信号，正在清理..."
    stop_all
    exit 0
}

# 注册清理函数
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    local command="${1:-start}"
    
    case "$command" in
        start)
            print_info "开始启动ATS服务..."
            echo
            
            # 清理旧的PID文件
            rm -f "${PID_FILE}"
            
            # 启动服务
            start_docker
            sleep 2
            
            start_backend
            sleep 2
            
            start_frontend
            sleep 2
            
            # Agent服务可选启动
            if [ "${START_AGENT:-false}" = "true" ] || [ -n "${AGENT_TOKEN:-}" ]; then
                start_agent
            else
                print_info "跳过Agent启动（设置 START_AGENT=true 或 AGENT_TOKEN 环境变量来启动）"
            fi
            
            echo
            print_success "所有服务启动完成！"
            echo
            print_info "服务访问地址:"
            echo "  前端: http://localhost:5173"
            echo "  后端API: http://localhost:8000"
            echo "  后端文档: http://localhost:8000/api/v1/docs"
            echo "  Docker服务:"
            echo "    MySQL: localhost:3306"
            echo "    Redis: localhost:6379"
            echo "    RabbitMQ管理: http://localhost:15672"
            echo "    MinIO控制台: http://localhost:9001"
            echo
            print_info "查看日志: tail -f ${LOG_DIR}/*.log"
            print_info "停止服务: $0 stop"
            print_info "查看状态: $0 status"
            ;;
        stop)
            stop_all
            ;;
        status)
            show_status
            ;;
        restart)
            stop_all
            sleep 2
            $0 start
            ;;
        *)
            echo "用法: $0 {start|stop|status|restart}"
            echo
            echo "命令:"
            echo "  start   - 启动所有服务"
            echo "  stop    - 停止所有服务"
            echo "  status  - 查看服务状态"
            echo "  restart - 重启所有服务"
            echo
            echo "环境变量:"
            echo "  AGENT_TOKEN        - Agent连接令牌"
            echo "  AGENT_SERVER_URL   - Agent服务器地址 (默认: ws://localhost:8000/ws/agent)"
            echo "  START_AGENT        - 是否启动Agent (true/false)"
            echo
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
