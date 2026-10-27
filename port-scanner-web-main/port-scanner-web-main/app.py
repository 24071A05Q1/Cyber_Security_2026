from flask import Flask, render_template, request
from utils import validate_target, parse_port_range
from scanner import run_port_scanner

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    duration = None
    target_ip = None
    error_message = None
    
    if request.method == "POST":
        target = request.form.get("target", "").strip()
        ports_input = request.form.get("ports", "common").strip()
        
        try:
            target_ip = validate_target(target)
            ports_list = parse_port_range(ports_input)
            results, duration = run_port_scanner(ip=target_ip, ports=ports_list, max_threads=100, timeout=0.8)
        except Exception as e:
            error_message = str(e)
            
    return render_template("index.html", results=results, duration=duration, target_ip=target_ip, error=error_message)

if __name__ == "__main__":
    app.run(debug=True, port=5000)