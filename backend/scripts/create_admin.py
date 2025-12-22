"""创建管理员用户脚本"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Role, Permission, UserRole, RolePermission
from core.security import get_password_hash
from core.permissions import SYSTEM_PERMISSIONS

# 系统角色定义
SYSTEM_ROLES = {
    "admin": {
        "name": "系统管理员",
        "description": "拥有所有系统权限的管理员角色",
        "permissions": list(SYSTEM_PERMISSIONS.keys())
    }
}


def init_permissions(db: Session) -> dict[str, Permission]:
    """初始化系统权限"""
    permissions = {}
    
    for code, name in SYSTEM_PERMISSIONS.items():
        # 检查权限是否已存在
        existing = db.query(Permission).filter(Permission.code == code).first()
        if existing:
            permissions[code] = existing
            print(f"权限已存在: {code} - {name}")
        else:
            # 解析权限代码
            resource, action = code.split(":", 1)
            
            # 创建新权限
            permission = Permission(
                code=code,
                name=name,
                resource=resource,
                action=action,
                description=f"{name}权限"
            )
            db.add(permission)
            permissions[code] = permission
            print(f"创建权限: {code} - {name}")
    
    db.commit()
    return permissions


def init_roles(db: Session, permissions: dict[str, Permission]) -> dict[str, Role]:
    """初始化系统角色"""
    roles = {}
    
    for role_name, role_data in SYSTEM_ROLES.items():
        # 检查角色是否已存在
        existing = db.query(Role).filter(Role.name == role_name).first()
        if existing:
            roles[role_name] = existing
            print(f"角色已存在: {role_name} - {role_data['name']}")
            
            # 确保角色有所有权限
            for perm_code in role_data["permissions"]:
                if perm_code in permissions:
                    perm = permissions[perm_code]
                    # 检查角色权限关联是否已存在
                    existing_rp = db.query(RolePermission).filter(
                        RolePermission.role_id == existing.id,
                        RolePermission.permission_id == perm.id
                    ).first()
                    if not existing_rp:
                        rp = RolePermission(role_id=existing.id, permission_id=perm.id)
                        db.add(rp)
                        print(f"  添加权限: {perm_code}")
        else:
            # 创建新角色
            role = Role(
                name=role_name,
                display_name=role_data["name"],
                description=role_data.get("description", ""),
                is_system=True
            )
            db.add(role)
            db.flush()  # 获取角色ID
            roles[role_name] = role
            print(f"创建角色: {role_name} - {role_data['name']}")
            
            # 为角色分配权限
            for perm_code in role_data["permissions"]:
                if perm_code in permissions:
                    perm = permissions[perm_code]
                    rp = RolePermission(role_id=role.id, permission_id=perm.id)
                    db.add(rp)
                    print(f"  分配权限: {perm_code}")
    
    db.commit()
    return roles


def create_admin_user(
    db: Session,
    username: str = "admin",
    email: str = "admin@example.com",
    password: str = "admin123",
    full_name: str = "系统管理员"
) -> User:
    """创建管理员用户"""
    # 检查用户是否已存在
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        print(f"用户已存在: {username} ({existing_user.email})")
        user = existing_user
    else:
        # 创建新用户
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            full_name=full_name,
            status=True
        )
        db.add(user)
        db.flush()  # 获取用户ID
        print(f"创建用户: {username} ({email})")
    
    # 获取管理员角色
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        raise Exception("管理员角色不存在，请先初始化角色")
    
    # 检查用户是否已有管理员角色
    existing_user_role = db.query(UserRole).filter(
        UserRole.user_id == user.id,
        UserRole.role_id == admin_role.id
    ).first()
    
    if not existing_user_role:
        user_role = UserRole(user_id=user.id, role_id=admin_role.id)
        db.add(user_role)
        print(f"分配管理员角色给用户: {username}")
    else:
        print(f"用户已有管理员角色: {username}")
    
    db.commit()
    return user


def main():
    """主函数"""
    print("=" * 50)
    print("开始创建管理员用户")
    print("=" * 50)
    
    db: Session = SessionLocal()
    try:
        # 1. 初始化权限
        print("\n1. 初始化系统权限...")
        permissions = init_permissions(db)
        
        # 2. 初始化角色
        print("\n2. 初始化系统角色...")
        roles = init_roles(db, permissions)
        
        # 3. 创建管理员用户
        print("\n3. 创建管理员用户...")
        # 可以通过环境变量或命令行参数自定义
        username = os.getenv("ADMIN_USERNAME", "admin")
        email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        password = os.getenv("ADMIN_PASSWORD", "admin123")
        full_name = os.getenv("ADMIN_FULL_NAME", "系统管理员")
        
        user = create_admin_user(db, username, email, password, full_name)
        
        print("\n" + "=" * 50)
        print("管理员用户创建成功！")
        print("=" * 50)
        print(f"用户名: {user.username}")
        print(f"邮箱: {user.email}")
        print(f"密码: {password}")
        print(f"角色: 系统管理员")
        print("=" * 50)
        print("\n提示: 首次登录后请及时修改密码！")
        
    except Exception as e:
        db.rollback()
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

