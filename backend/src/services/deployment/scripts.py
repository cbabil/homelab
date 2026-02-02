"""
Batched Shell Scripts

Shell scripts for Docker operations, designed to run in a single SSH connection.
This prevents overwhelming sshd with many rapid connections.
"""


def cleanup_container_script(container_name: str, image: str = None) -> str:
    """Build script to clean up a failed container.

    Args:
        container_name: Container to remove
        image: Optional image to remove

    Returns:
        Shell script string
    """
    script = f'''
docker stop {container_name} 2>/dev/null || true
docker rm -v {container_name} 2>/dev/null || true
'''
    if image:
        script += f'docker rmi {image} 2>/dev/null || true\n'

    script += 'echo "CLEANUP_DONE"'
    return script


def create_container_script(run_cmd: str) -> str:
    """Build script to prune images and create container.

    Args:
        run_cmd: Docker run command

    Returns:
        Shell script string
    """
    return f'''
# Prune dangling images (cleanup from pull)
docker image prune -f > /dev/null 2>&1 || true

# Run the container
CONTAINER_ID=$({run_cmd})
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS:$CONTAINER_ID"
else
    echo "FAILED:$EXIT_CODE"
fi
'''


def status_check_script(container_id: str) -> str:
    """Build script to check container status and health.

    Args:
        container_id: Container ID to check

    Returns:
        Shell script string
    """
    return f'''
STATUS=$(docker inspect --format='{{{{.State.Status}}}}' {container_id} 2>/dev/null || echo "unknown")
HEALTH=$(docker inspect --format='{{{{.State.Health.Status}}}}' {container_id} 2>/dev/null || echo "none")
RESTARTS=$(docker inspect --format='{{{{.RestartCount}}}}' {container_id} 2>/dev/null || echo "0")
echo "STATUS:$STATUS"
echo "HEALTH:$HEALTH"
echo "RESTARTS:$RESTARTS"
if [ "$STATUS" = "exited" ] || [ "$STATUS" = "dead" ] || [ "$STATUS" = "restarting" ] || [ "$HEALTH" = "unhealthy" ] || [ "$RESTARTS" -gt "0" ]; then
    echo "LOGS:$(docker logs --tail 10 {container_id} 2>&1 | head -c 500)"
fi
'''


def uninstall_script(container_name: str, remove_data: bool = True) -> str:
    """Build script to fully uninstall an app.

    Uses docker inspect format options for reliable data extraction.
    Removes container, unused volumes, unused networks, and unused image.

    Args:
        container_name: Container to uninstall
        remove_data: Whether to remove volumes

    Returns:
        Shell script string
    """
    script = f'''#!/bin/bash
set -e

# Get container info using docker inspect with specific format options
IMAGE_NAME=$(docker inspect --format '{{{{.Config.Image}}}}' {container_name} 2>/dev/null || echo "")
VOLUMES=$(docker inspect --format '{{{{range .Mounts}}}}{{{{if eq .Type "volume"}}}}{{{{.Name}}}} {{{{end}}}}{{{{end}}}}' {container_name} 2>/dev/null || echo "")
NETWORKS=$(docker inspect --format '{{{{range $k, $v := .NetworkSettings.Networks}}}}{{{{$k}}}} {{{{end}}}}' {container_name} 2>/dev/null || echo "")

echo "IMAGE:$IMAGE_NAME"
echo "VOLUMES:$VOLUMES"
echo "NETWORKS:$NETWORKS"

# Stop and remove container
docker stop {container_name} 2>/dev/null || true
docker rm {container_name} 2>/dev/null || true
echo "REMOVED:container:{container_name}"

# Small delay to let Docker release resources
sleep 1
'''

    if remove_data:
        script += '''
# Remove unused volumes
for VOL in $VOLUMES; do
    if [ -n "$VOL" ]; then
        USERS=$(docker ps -a --filter volume=$VOL --format '{{.Names}}' 2>/dev/null)
        if [ -z "$USERS" ]; then
            docker volume rm $VOL 2>/dev/null && echo "REMOVED:volume:$VOL" || true
        else
            echo "SKIPPED:volume:$VOL (in use)"
        fi
    fi
done
'''

    script += '''
# Remove unused custom networks
for NET in $NETWORKS; do
    if [ -n "$NET" ] && [ "$NET" != "bridge" ] && [ "$NET" != "host" ] && [ "$NET" != "none" ]; then
        COUNT=$(docker network inspect $NET --format '{{len .Containers}}' 2>/dev/null || echo "1")
        if [ "$COUNT" = "0" ]; then
            docker network rm $NET 2>/dev/null && echo "REMOVED:network:$NET" || true
        else
            echo "SKIPPED:network:$NET (in use)"
        fi
    fi
done

# Remove image if unused
if [ -n "$IMAGE_NAME" ]; then
    USERS=$(docker ps -a --filter ancestor=$IMAGE_NAME --format '{{.Names}}' 2>/dev/null)
    if [ -z "$USERS" ]; then
        docker rmi $IMAGE_NAME 2>/dev/null && echo "REMOVED:image:$IMAGE_NAME" || true
    else
        echo "SKIPPED:image:$IMAGE_NAME (in use)"
    fi
fi

echo "CLEANUP_COMPLETE"
'''

    return script


def cleanup_failed_deployment_script(container_name: str, image_name: str = None) -> str:
    """Build script to clean up a failed deployment.

    Args:
        container_name: Container to clean up
        image_name: Optional image to remove

    Returns:
        Shell script string
    """
    script = "#!/bin/bash\n"

    if container_name:
        script += f'''
# Stop and remove container
docker stop {container_name} 2>/dev/null || true
docker rm -f {container_name} 2>/dev/null && echo "CONTAINER_REMOVED" || true
sleep 1
'''

    if image_name:
        script += f'''
# Remove image if unused
USERS=$(docker ps -a --filter ancestor={image_name} -q 2>/dev/null | wc -l)
if [ "$USERS" = "0" ]; then
    docker rmi {image_name} 2>/dev/null && echo "IMAGE_REMOVED" || true
fi
'''

    script += '\necho "CLEANUP_DONE"'
    return script


def background_pull_script(image: str, job_id: str) -> str:
    """Build script to pull Docker image in background.

    Uses nohup to survive SSH disconnect. Creates status files for polling.
    Skips pull entirely if image already exists locally.

    Args:
        image: Docker image to pull
        job_id: Unique job identifier

    Returns:
        Shell script string
    """
    return f'''#!/bin/bash
WORK_DIR="/tmp/tomo"
mkdir -p "$WORK_DIR"

# Check if image already exists locally - skip pull entirely
if docker image inspect {image} > /dev/null 2>&1; then
    echo "0" > "$WORK_DIR/{job_id}.status"
    echo "Image already exists" > "$WORK_DIR/{job_id}.log"
    echo "IMAGE_EXISTS"
    exit 0
fi

# Check if already running
if [ -f "$WORK_DIR/{job_id}.pid" ]; then
    PID=$(cat "$WORK_DIR/{job_id}.pid")
    if kill -0 "$PID" 2>/dev/null; then
        echo "ALREADY_RUNNING:$PID"
        exit 0
    fi
fi

# Start pull in background with LOW priority and memory limits
nohup /bin/bash -c '
    # Limit memory usage of this shell
    ulimit -v 1048576 2>/dev/null || true
    ionice -c 3 nice -n 19 docker pull {image} > /tmp/tomo/{job_id}.log 2>&1
    echo $? > /tmp/tomo/{job_id}.status
' > /dev/null 2>&1 &

echo $! > "$WORK_DIR/{job_id}.pid"
echo "STARTED:$(cat $WORK_DIR/{job_id}.pid)"
'''


def poll_pull_status_script(job_id: str) -> str:
    """Build script to check background pull status.

    Args:
        job_id: Job identifier from background_pull_script

    Returns:
        Shell script string
    """
    return f'''#!/bin/bash
WORK_DIR="/tmp/tomo"
PID_FILE="$WORK_DIR/{job_id}.pid"
STATUS_FILE="$WORK_DIR/{job_id}.status"
LOG_FILE="$WORK_DIR/{job_id}.log"

if [ ! -f "$PID_FILE" ]; then
    echo "STATUS:not_found"
    exit 0
fi

PID=$(cat "$PID_FILE")

if [ -f "$STATUS_FILE" ]; then
    EXIT_CODE=$(cat "$STATUS_FILE")
    if [ "$EXIT_CODE" = "0" ]; then
        echo "STATUS:completed"
    else
        echo "STATUS:failed"
    fi
    echo "EXIT_CODE:$EXIT_CODE"
elif kill -0 "$PID" 2>/dev/null; then
    echo "STATUS:running"
    echo "PID:$PID"
else
    echo "STATUS:failed"
    echo "EXIT_CODE:-1"
fi

# Get progress from log (last 30 lines)
if [ -f "$LOG_FILE" ]; then
    echo "LOG_START"
    tail -n 30 "$LOG_FILE" 2>/dev/null
    echo "LOG_END"
fi
'''


def cleanup_pull_job_script(job_id: str) -> str:
    """Build script to clean up pull job files.

    Args:
        job_id: Job identifier

    Returns:
        Shell script string
    """
    return f'''#!/bin/bash
WORK_DIR="/tmp/tomo"
rm -f "$WORK_DIR/{job_id}.pid" "$WORK_DIR/{job_id}.status" "$WORK_DIR/{job_id}.log"
echo "CLEANED"
'''


def preflight_check_script(min_disk_gb: int = 5, min_memory_mb: int = 256) -> str:
    """Build script to check server resources before deployment.

    Args:
        min_disk_gb: Minimum free disk space in GB
        min_memory_mb: Minimum free memory in MB

    Returns:
        Shell script string
    """
    return f'''#!/bin/bash
# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR:DOCKER:Docker daemon not responding"
    exit 1
fi

# Check disk space
DOCKER_ROOT=$(docker info --format '{{{{.DockerRootDir}}}}' 2>/dev/null || echo "/var/lib/docker")
AVAIL_KB=$(df "$DOCKER_ROOT" 2>/dev/null | tail -1 | awk '{{print $4}}')
AVAIL_GB=$((AVAIL_KB / 1024 / 1024))

if [ "$AVAIL_GB" -lt {min_disk_gb} ]; then
    echo "ERROR:DISK:Only ${{AVAIL_GB}}GB free, need {min_disk_gb}GB"
    exit 1
fi

# Check memory
AVAIL_MB=$(free -m 2>/dev/null | awk '/^Mem:/ {{print $7}}' || echo "9999")

if [ "$AVAIL_MB" -lt {min_memory_mb} ]; then
    echo "ERROR:MEMORY:Only ${{AVAIL_MB}}MB free, need {min_memory_mb}MB"
    exit 1
fi

echo "OK:disk=${{AVAIL_GB}}GB,memory=${{AVAIL_MB}}MB"
'''


def health_check_script(container_name: str) -> str:
    """Build script to check container health comprehensively.

    Args:
        container_name: Container to check

    Returns:
        Shell script string
    """
    return f'''#!/bin/bash
# Get container status
STATUS=$(docker inspect --format '{{{{.State.Status}}}}' {container_name} 2>/dev/null || echo "not_found")
echo "STATUS:$STATUS"

# Get restart count
RESTARTS=$(docker inspect --format '{{{{.RestartCount}}}}' {container_name} 2>/dev/null || echo "0")
echo "RESTARTS:$RESTARTS"

# Get port mappings
PORTS=$(docker port {container_name} 2>/dev/null || echo "")
echo "PORTS:$PORTS"

# Get recent logs
LOGS=$(docker logs --tail 20 {container_name} 2>&1 | head -c 2000)
echo "LOGS_START"
echo "$LOGS"
echo "LOGS_END"
'''
