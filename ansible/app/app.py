# 导入标准库
import os                     # 用于读取系统环境变量

# 导入 Flask 框架及相关工具
from flask import Flask, jsonify, Response  # Flask：Web 框架；jsonify：返回 JSON 响应；Response：自定义响应类型

# 导入 psycopg2，用于连接 PostgreSQL 数据库
import psycopg2

# 导入 Prometheus 监控相关组件
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
# Counter：计数器指标，用于统计请求次数
# generate_latest：生成最新的 Prometheus 指标数据
# CONTENT_TYPE_LATEST：定义返回数据的 MIME 类型（Prometheus 指标专用）

# 创建一个 Flask 应用实例
app = Flask(__name__)

# 定义 Prometheus 监控指标
# 定义一个名为 app_requests_total 的计数器，用来统计 HTTP 请求总数
REQUEST_COUNT = Counter('app_requests_total', 'Total HTTP Requests')


# 定义函数：获取数据库连接
def get_db_connection():
    """
    从环境变量中读取 PostgreSQL 数据库连接配置，
    然后尝试建立数据库连接。
    如果连接成功，返回连接对象；失败则返回 None。
    """
    db_config = {
        'host': os.getenv('DB_HOST'),            # 数据库主机名，默认 localhost
        'database': os.getenv('POSTGRES_DB'),           # 数据库名称，默认 pg
        'user': os.getenv('POSTGRES_USER' ),            # 数据库用户名，默认 ldl
        'password': os.getenv('POSTGRES_PASSWORD'), # 数据库密码
        'port': os.getenv('POSTGRES_PORT')            # 数据库端口号，默认 5432
        }
    
    try:
        # 尝试建立数据库连接
        conn = psycopg2.connect(**db_config)
        return conn
    except Exception as e:
        # 如果连接失败，打印错误信息并返回 None
        print(f"Database connection error: {e}")
        return None


# 定义 Flask 路由：主页 /
@app.route('/')
def index():
    """
    应用的根路径：
    1. 增加请求计数器（Prometheus 统计用）
    2. 连接数据库并查询 PostgreSQL 版本信息
    3. 返回 JSON 格式的响应，包括：
       - 欢迎信息
       - 数据库版本号
       - 当前主机名（容器名）
    """
    REQUEST_COUNT.inc()  # 每收到一次请求，请求计数器 +1

    # 获取数据库连接
    conn = get_db_connection()
    if conn:
        try:
            # 查询 PostgreSQL 数据库版本
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()

            # 关闭游标和连接
            cur.close()
            conn.close()

            # 返回 JSON 响应
            return jsonify({
                'message': 'Hello from Python app!', 
                'db_version': version[0],                     # PostgreSQL 版本信息
                'host': os.getenv('HOSTNAME', 'unknown')       # 获取当前容器的主机名
            })
        except Exception as e:
            # SQL 查询或其他异常
            return jsonify({'error': str(e)}), 500
    else:
        # 数据库连接失败
        return jsonify({'error': 'Database connection failed'}), 500


# 定义 Flask 路由：/metrics
@app.route('/metrics')
def metrics():
    """
    提供 Prometheus 可抓取的监控指标接口。
    Prometheus 会定期访问这个路径 (/metrics) 来采集应用指标。
    """
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


# 定义 Flask 路由：/health
@app.route('/health')
def health():
    """
    健康检查接口，用于外部探测服务（如 Docker、Kubernetes、Nginx）
    判断应用是否健康。
    """
    return jsonify({'status': 'healthy'})


# 应用启动入口
if __name__ == "__main__":
    # 启动 Flask 应用，监听所有网卡地址的 5000 端口
    # host='0.0.0.0'
    app.run(host='0.0.0.0', port=5555)
