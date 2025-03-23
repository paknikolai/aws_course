from flask import Flask, render_template, jsonify

app = Flask(__name__)

def get_region():
    try:
        from ec2_metadata import ec2_metadata
        return f"region: {ec2_metadata.region} AZ: {ec2_metadata.availability_zone}"
    except Exception as e:
        return "can't get region because of " + repr(e)

@app.route("/")
def index():
    message = get_region()
    return render_template("index.html", message=message)

@app.route("/health")
def health_check():
    """Endpoint for health checks."""
    return jsonify({"status": get_region()}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)