from flask import Flask, request, render_template_string, redirect, url_for
import subprocess

app = Flask(__name__)
latest_inputs = {
    'mrn': '',
    'topic': 'patientchart',
    'sub': 'vitas-servicebus-rentalresult',
    'x': '1',
    'command': '',
    'file': '',
    'env': 'qa'
}
command_history = []
command_id = 0

template = '''<!doctype html>
<html>
    <head>
        <title>Execute sbTest.exe</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }
            header {
                background-color: #333;
                color: white;
                font-size: 1.5rem;
                padding: 1rem 2rem;
            }
            main {
                padding: 2rem;
            }
            form div {
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
            }
            label {
                width: 100px;
                font-weight: bold;
            }
            input, input.list {
                flex-grow: 1;
                padding: 0.5rem;
                border-radius: 5px;
                border: 1px solid #ccc;
            }
            input.highlight {
                background-color: #ffffcc;
            }
            button {
                background-color: #007BFF;
                border: none;
                border-radius: 5px;
                color: white;
                cursor: pointer;
                font-size: 1rem;
                padding: 0.5rem 1rem;
                text-align: center;
                margin-top: 1rem;
            }
            button:hover {
                background-color: #0056b3;
            }
            pre {
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 1rem;
            }
            h2 {
                margin-top: 2rem;
            }
            a {
                color: #007BFF;
                text-decoration: none;
            }
            a:hover {
                color: #0056b3;
                text-decoration: underline;
            }
            .caption {
                font-size: 0.8rem;
                color: #777;
            }
        </style>
    </head>
    <body>
        <header>
            Execute sbTest.exe with Parameters
        </header>
        <main>
            <form method="POST">
                {% for key in latest_inputs.keys() %}
                    {% if key != 'sub' %}
                        <div>
                            <label for="{{ key }}">{{ key }}:</label>
                            <input id="{{ key }}" name="{{ key }}" value="{{ latest_inputs[key] }}" class="{{ 'highlight' if key == 'mrn' or key == 'x' else '' }}" />
                            {% if key == 'mrn' %}
                                <span class="caption">VITAS Patient ID</span>
                            {% elif key == 'x' %}
                                <span class="caption">Amount of requests to send</span>
                            {% endif %}
                        </div>
                    {% else %}
                        <div>
    <label for="sub">Sub:</label>
    <select id="sub" name="sub">
        <option value="{{ latest_inputs['sub'] }}" selected>{{ latest_inputs['sub'] }}</option>
        <option value="vitas-servicebus-WellSky-patient-outbound">vitas-servicebus-WellSky-patient-outbound</option>
        <option value="vitas-servicebus-rentalresult">vitas-servicebus-rentalresult</option>
    </select>
    <span class="caption">Subscription name</span>
</div>
                    {% endif %}
                {% endfor %}
                <button type="submit">Execute</button>
            </form>
            {% if output %}
                <h2>Output:</h2>
                <pre>{{ output }}</pre>
            {% endif %}
            {% if command_history %}
                <h2>Command History (Click on item to re-run request):</h2>
                <ol>
                    {% for command in command_history %}
                        <li><a href="{{ url_for('re_execute', command_id=command.id) }}">{{ command.text }}</a></li>
                    {% endfor %}
                </ol>
            {% endif %}
        </main>
    </body>
</html>
'''
@app.route('/', methods=['GET', 'POST'])
def index():
    global latest_inputs, command_history
    output = None
    if request.method == 'POST':
        command = ''
        for key in latest_inputs.keys():
            value = request.form.get(key, '')
            if value:
                command += f' -{key} {value}'
                latest_inputs[key] = value  # save the latest inputs

        if command:
            output = execute_command(command.strip())
            add_command_to_history(command)

    return render_template_string(template, output=output, latest_inputs=latest_inputs, command_history=command_history)


@app.route('/re_execute/<int:command_id>', methods=['GET'])
def re_execute(command_id):
    command= get_command_from_history(command_id)
    if command:
        output = execute_command(command)
        return render_template_string(template, output=output, latest_inputs=latest_inputs, command_history=command_history)
    else:
        return redirect(url_for('index'))


def execute_command(command):
    exe_path = 'sbTest.exe'
    arguments = command.strip().split()

    try:
        result = subprocess.run([exe_path] + arguments, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.strip()}"


def add_command_to_history(command):
    global command_history, command_id
    command_history.insert(0, {'id': command_id, 'text': command})
    command_id += 1


def get_command_from_history(command_id):
    for item in command_history:
        if item['id'] == command_id:
            return item['text']
    return None


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')