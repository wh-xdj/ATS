-- 添加git_enabled字段到test_suites表
-- 用于标记Git配置是否启用，避免关闭开关时清空配置

ALTER TABLE `test_suites`
ADD COLUMN `git_enabled` VARCHAR(10) NOT NULL DEFAULT 'false' 
COMMENT 'Git配置是否启用: true/false';

-- 对于已有数据，如果git_repo_url和git_branch都存在，则设置为true
UPDATE `test_suites`
SET `git_enabled` = 'true'
WHERE `git_repo_url` IS NOT NULL 
  AND `git_repo_url` != '' 
  AND `git_branch` IS NOT NULL 
  AND `git_branch` != '';

