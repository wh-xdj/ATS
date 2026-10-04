"""Project access for newly connected read/report/execute endpoints."""
from fastapi import HTTPException
from models.project import Project
from core.permissions import has_global_permission, has_project_permission


def require_project(db, user, project_id, resource='test_execution', action='read'):
    project = db.get(Project, str(project_id))
    if not project:
        raise HTTPException(404, '项目不存在')
    if project.owner_id != str(user.id) and not (
        has_global_permission(db, user.id, resource, action)
        or has_project_permission(db, user.id, project.id, resource, action)
    ):
        raise HTTPException(403, '没有项目权限')
    return project
