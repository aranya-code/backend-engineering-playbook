# Configuration Management

Production workflows for managing, validating, diffing, and rolling back Nginx configurations.

---

# Configuration File Locations

```text
/etc/nginx/                          # Main config directory
├── nginx.conf                       # Primary config file (entry point)
├── conf.d/                          # Drop-in server block configs (*.conf auto-included)
│   ├── default.conf                 # Default server block
│   ├── api.example.com.conf         # API virtual host
│   └── admin.example.com.conf       # Admin virtual host
├── sites-available/                 # Available virtual hosts (Debian/Ubuntu only)
├── sites-enabled/                   # Symlinks to active virtual hosts
├── snippets/                        # Reusable config fragments
│   ├── ssl-params.conf              # Shared SSL settings
│   └── proxy-params.conf            # Shared proxy headers
├── modules-enabled/                 # Loaded dynamic modules
└── mime.types                       # MIME type mappings
```

**Best Practice**: Use `conf.d/*.conf` for server blocks instead of editing `nginx.conf` directly. One file per virtual host. This makes configuration modular and easier to manage.

---

# Include Directive

The `include` directive pulls in external configuration files:

```nginx
# Include all .conf files in conf.d/
include /etc/nginx/conf.d/*.conf;

# Include a specific snippet
include /etc/nginx/snippets/ssl-params.conf;

# Include from sites-enabled (Debian/Ubuntu pattern)
include /etc/nginx/sites-enabled/*;
```

## Reusable Snippets

Create shared configuration fragments to avoid duplication:

```nginx
# /etc/nginx/snippets/proxy-params.conf
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_http_version 1.1;
proxy_connect_timeout 60s;
proxy_read_timeout 60s;
```

```nginx
# In your server block:
location /api/ {
    include /etc/nginx/snippets/proxy-params.conf;
    proxy_pass http://backend_api;
}
```

---

# Configuration Testing Workflow

## The Golden Rule

```bash
# NEVER reload without testing first
sudo nginx -t && sudo nginx -s reload
```

## Full Validation Workflow

```bash
# Step 1: Edit configuration
sudo vim /etc/nginx/conf.d/api.example.com.conf

# Step 2: Test syntax
sudo nginx -t
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# Step 3: Dump and review full resolved config (optional, for complex changes)
sudo nginx -T | less

# Step 4: Reload
sudo nginx -s reload

# Step 5: Verify the change
curl -I https://api.example.com/health
```

---

# Diff Workflow (Before and After)

Compare configuration before and after changes:

```bash
# Before making changes — save current resolved config
sudo nginx -T > /tmp/nginx-before.conf

# Make your changes
sudo vim /etc/nginx/conf.d/api.example.com.conf

# After changes — save new resolved config
sudo nginx -T > /tmp/nginx-after.conf

# Compare
diff /tmp/nginx-before.conf /tmp/nginx-after.conf

# Or use a side-by-side diff
diff --side-by-side /tmp/nginx-before.conf /tmp/nginx-after.conf | less
```

---

# Rollback Strategy

## Simple Rollback (Single File)

```bash
# Before editing, create a timestamped backup
sudo cp /etc/nginx/conf.d/api.example.com.conf \
        /etc/nginx/conf.d/api.example.com.conf.bak.$(date +%Y%m%d_%H%M%S)

# If something goes wrong, restore
sudo cp /etc/nginx/conf.d/api.example.com.conf.bak.20260718_120000 \
        /etc/nginx/conf.d/api.example.com.conf
sudo nginx -t && sudo nginx -s reload
```

## Git-Based Rollback (Recommended)

```bash
# Initialize git in the config directory
cd /etc/nginx
sudo git init
sudo git add .
sudo git commit -m "Initial configuration"

# Before changes
sudo git add -A && sudo git commit -m "Before: adding rate limiting to API"

# Make changes
sudo vim conf.d/api.example.com.conf

# If test fails, rollback
sudo git checkout -- conf.d/api.example.com.conf
sudo nginx -t && sudo nginx -s reload

# If test passes, commit
sudo git add -A && sudo git commit -m "Added rate limiting to API (100 req/min)"
```

---

# Enabling and Disabling Sites (Debian/Ubuntu)

```bash
# Enable a site (create symlink)
sudo ln -s /etc/nginx/sites-available/api.example.com.conf \
           /etc/nginx/sites-enabled/api.example.com.conf

# Disable a site (remove symlink, config preserved)
sudo rm /etc/nginx/sites-enabled/api.example.com.conf

# Reload after enabling/disabling
sudo nginx -t && sudo nginx -s reload
```

**Note**: On RHEL/CentOS/Amazon Linux, there is no `sites-available/sites-enabled` pattern. Use `conf.d/*.conf` instead.

---

# Checking What Config Nginx is Using

```bash
# What config file is Nginx currently running with?
sudo nginx -T 2>&1 | head -5
# Output: # configuration file /etc/nginx/nginx.conf:

# What PID file is active?
cat /run/nginx.pid

# What is the running Nginx binary path?
which nginx
# /usr/sbin/nginx

# What user is Nginx running as?
ps aux | grep "nginx: worker" | awk '{print $1}' | head -1
# www-data (or nginx)
```

---

# Environment-Specific Configurations

For different environments (staging, production), use separate config files or environment variables:

```bash
# Use envsubst to template Nginx configs
export BACKEND_HOST=api-staging.internal
export BACKEND_PORT=8080

envsubst '${BACKEND_HOST} ${BACKEND_PORT}' \
    < /etc/nginx/templates/api.conf.template \
    > /etc/nginx/conf.d/api.conf

sudo nginx -t && sudo nginx -s reload
```

Template file (`api.conf.template`):
```nginx
upstream backend {
    server ${BACKEND_HOST}:${BACKEND_PORT};
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://backend;
    }
}
```

---

# Common Mistakes

- Editing `nginx.conf` directly instead of using modular `conf.d/*.conf` files. Makes rollback and review much harder.
- Not using `nginx -t` before `nginx -s reload`. A syntax error will fail the reload silently.
- Forgetting to create backups before editing production config. Git-track `/etc/nginx/` from day one.
- Using `sites-enabled` symlinks on RHEL/CentOS where the pattern doesn't exist by default.
- Hardcoding environment-specific values (IPs, ports) instead of using `envsubst` templates.

---

# Key Takeaways

- One server block per file in `conf.d/`. Never pile everything into `nginx.conf`.
- Use `include` and snippets for shared configuration (SSL params, proxy headers).
- Always `nginx -t && nginx -s reload` — never reload without testing.
- Git-track `/etc/nginx/` for instant rollback and change history.
- Use `nginx -T` to dump the full resolved configuration — essential for debugging include chains.
- Use `envsubst` for environment-specific templating (staging vs production).

---
