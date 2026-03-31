"""Constants for the Kaneo integration."""

DOMAIN = "kaneo"
CONF_BASE_URL = "base_url"
CONF_API_TOKEN = "api_token"
CONF_WORKSPACE_ID = "workspace_id"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 300  # 5 minutes
DEFAULT_BASE_URL = "https://cloud.kaneo.app"

# API endpoints
API_SESSION = "/api/auth/get-session"
API_PROJECTS = "/api/project"
API_TASKS = "/api/task/tasks/{project_id}"

# Sensor attributes
ATTR_TASK_ID = "task_id"
ATTR_TASK_TITLE = "title"
ATTR_TASK_STATUS = "status"
ATTR_TASK_PRIORITY = "priority"
ATTR_TASK_DUE_DATE = "due_date"
ATTR_TASK_PROJECT = "project"
ATTR_TASK_ASSIGNEE = "assignee"
ATTR_TASK_DESCRIPTION = "description"
ATTR_TASK_CREATED_AT = "created_at"
ATTR_TOTAL_TASKS = "total_tasks"
ATTR_TASKS_LIST = "tasks"
