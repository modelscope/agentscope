#!/bin/bash
set -e

# 定义文件路径
SQL_FILE_PATH="mysql-init/insert_data.sql"
PUBLIC_KEY_PATH="../app/utils/keys/public.pem"
ENCRYPT_SCRIPT_PATH="../app/utils/crypto.py"
HASH_PASSWORD_PATH="../app/utils/security.py"
ENV_FILE="../.env"

# 检查.env文件是否存在
if [ ! -f "$ENV_FILE" ]; then
  echo ".env file not found at $ENV_FILE!"
  exit 1
fi

# 从.env文件加载MySQL凭据
source "$ENV_FILE"

# 检查必要文件是否存在
for file in "$SQL_FILE_PATH" "$PUBLIC_KEY_PATH"; do
  if [ ! -f "$file" ]; then
    echo "Required file not found at $file!"
    exit 1
  fi
done

# 使用Python脚本生成加密的API_KEY和密码
function encrypt {
  local content="$1"
  python -c "
import sys
sys.path.insert(0, '$(dirname "$ENCRYPT_SCRIPT_PATH")')
from crypto import encrypt_with_rsa
print(encrypt_with_rsa('$content'))
"
}

ENCRYPTED_API_KEY=$(encrypt "${DASHSCOPE_API_KEY}")

function hash_encrypt {
  local password="$1"
  python -c "
import sys
sys.path.insert(0, '$(dirname "$HASH_PASSWORD_PATH")')
from security import get_password_hash
print(get_password_hash('$password'))
"
}
ENCRYPTED_PASSWORD=$(hash_encrypt "123456")

# 检查加密结果
for var in ENCRYPTED_API_KEY ENCRYPTED_PASSWORD; do
  if [ -z "${!var}" ]; then
    echo "Failed to encrypt $var."
    exit 1
  fi
done

# 输出加密的API_KEY的前30个字符
echo "Encrypted API_KEY: ${ENCRYPTED_API_KEY:0:30}..."

# MySQL连接参数
MYSQL_HOST="127.0.0.1"
MYSQL_USER="${MYSQL_USER}"
MYSQL_PASS="${MYSQL_PASSWORD}"
MYSQL_DB="${MYSQL_DATABASE:-agentscope}"

echo "try to connect MySQL: Host=$MYSQL_HOST, Port=$MYSQL_PORT,
User=$MYSQL_USER, Password=$MYSQL_PASS, DB=$MYSQL_DB"

# 等待MySQL准备就绪
echo "Waiting for MySQL to be ready..."
until mysqladmin ping -h"$MYSQL_HOST" -u"$MYSQL_USER" -p"$MYSQL_PASS" --silent; do
  echo "MySQL is unavailable - sleeping"
  sleep 2
done

# 检查并插入数据
echo "Checking table structure..."
mysql -h"$MYSQL_HOST" -u"$MYSQL_USER" -p"$MYSQL_PASS" "$MYSQL_DB" -e "DESCRIBE account;"

echo "Checking if table exists and is empty..."
COUNT=$(mysql -h"$MYSQL_HOST" -u"$MYSQL_USER" -p"$MYSQL_PASS" "$MYSQL_DB" -N -e "SELECT COUNT(*) FROM account;")
if [ "$COUNT" -eq "0" ]; then
  echo "Table is empty, inserting data..."
  CURRENT_TIME=$(date '+%Y-%m-%d %H:%M:%S')

  # 替换SQL文件中的占位符
  sed "s|{CURRENT_TIME}|$CURRENT_TIME|g; s|{API_KEY}|$ENCRYPTED_API_KEY|g;
  s|{PASSWORD}|$ENCRYPTED_PASSWORD|g" "$SQL_FILE_PATH" > temp_insert.sql

  # 插入数据并验证
  if mysql -h"$MYSQL_HOST" -u"$MYSQL_USER" -p"$MYSQL_PASS" "$MYSQL_DB" < temp_insert.sql; then
    echo "Data inserted successfully"
    echo "Verifying inserted data:"
    mysql -h"$MYSQL_HOST" -u"$MYSQL_USER" -p"$MYSQL_PASS" "$MYSQL_DB" -e "SELECT account_id, username, email, type, status, gmt_create, gmt_modified FROM account;"
  else
    echo "Error inserting data"
    exit 1
  fi
  rm temp_insert.sql
else
  echo "Table already has data"
  echo "Current data in table:"
  mysql -h"$MYSQL_HOST" -u"$MYSQL_USER" -p"$MYSQL_PASS" "$MYSQL_DB" -e "SELECT account_id, username, email, type, status, gmt_create, gmt_modified FROM account;"
fi