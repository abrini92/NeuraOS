package neura.motor

import future.keywords.if
import future.keywords.in

# Whitelisted apps per OS
allowed_apps_mac := ["Terminal", "Notes", "TextEdit", "VSCode", "Calculator"]
allowed_apps_linux := ["gedit", "kate", "code", "xterm", "gnome-terminal"]

# Allowed action types
allowed_actions := ["type_text", "click", "open_app"]

# Blocked text patterns
blocked_patterns := ["rm -rf", "curl | bash", "sudo ", "DROP TABLE", "/etc/", "/System/"]

# Main authorization rule
default allow := false

# Allow if all conditions met
allow if {
    action_is_allowed
    app_is_whitelisted
    not has_blocked_pattern
    not is_execute_command
    approval_check_passed
}

# Check action type is allowed
action_is_allowed if {
    input.action in allowed_actions
}

# Check app is whitelisted based on OS
app_is_whitelisted if {
    input.os == "mac"
    input.app in allowed_apps_mac
}

app_is_whitelisted if {
    input.os == "linux"
    input.app in allowed_apps_linux
}

# Allow if no app specified (e.g., click action)
app_is_whitelisted if {
    not input.app
}

# Check for blocked patterns in text
has_blocked_pattern if {
    some pattern in blocked_patterns
    contains(input.text, pattern)
}

# Block execute_command by default
is_execute_command if {
    input.action == "execute_command"
}

# Approval check: critical actions require user_approved
approval_check_passed if {
    not input.critical
}

approval_check_passed if {
    input.critical
    input.user_approved == true
}

# Reason for denial
reason := msg if {
    not allow
    not action_is_allowed
    msg := sprintf("Action '%s' not allowed", [input.action])
} else := msg if {
    not allow
    is_execute_command
    msg := "execute_command is blocked by default for security"
} else := msg if {
    not allow
    not app_is_whitelisted
    msg := sprintf("App '%s' not in whitelist for OS '%s'", [input.app, input.os])
} else := msg if {
    not allow
    has_blocked_pattern
    msg := "Text contains blocked pattern"
} else := msg if {
    not allow
    not approval_check_passed
    msg := "Critical action requires user approval"
} else := "Allowed" if {
    allow
}

# List of all violations
violations[msg] if {
    not action_is_allowed
    msg := sprintf("Action '%s' not in allowed list", [input.action])
}

violations[msg] if {
    is_execute_command
    msg := "execute_command is blocked"
}

violations[msg] if {
    input.app
    not app_is_whitelisted
    msg := sprintf("App '%s' not whitelisted", [input.app])
}

violations[msg] if {
    has_blocked_pattern
    msg := "Text contains dangerous pattern"
}

violations[msg] if {
    input.critical
    not input.user_approved
    msg := "User approval required for critical action"
}
