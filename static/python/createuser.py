from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route('/', methods=['POST'])
def create_user():
    name = request.form['name']
    password = request.form['password']
    email = request.form['email']
    role = request.form['role']
    
    # Check if user creation is successful (You can modify this logic)
    user_created = True
    
    if user_created:
        # Render a success message with JavaScript to display the pop-up
        success_message = "User created successfully!"
        return render_template_string("""
        <script>
            window.onload = function() {
                var popup = document.getElementById("popup");
                var popupMessage = document.getElementById("popup-message");
                popupMessage.innerText = "{{ success_message }}";
                popup.style.display = "block";

                var closePopup = document.getElementById("close-popup");
                closePopup.onclick = function() {
                    popup.style.display = "none";
                };
            }
        </script>
        """, success_message=success_message)
    else:
        # Handle the case where user creation failed
        return "User creation failed"

if __name__ == '__main__':
    app.run()
