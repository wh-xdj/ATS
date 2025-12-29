-- 将测试套表中的git字段改为可选
-- 允许测试套不配置git仓库，直接在工作目录中执行命令

ALTER TABLE `test_suites`
MODIFY COLUMN `git_repo_url` VARCHAR(500) NULL COMMENT 'Git代码仓库地址（可选）';

ALTER TABLE `test_suites`
MODIFY COLUMN `git_branch` VARCHAR(100) NULL DEFAULT 'main' COMMENT 'Git分支（可选）';

ALTER TABLE `test_suites`
MODIFY COLUMN `git_token` TEXT NULL COMMENT 'Git登录Token（可选）';

