from flask import Blueprint, request, jsonify
import json, smtplib
from config import TICKET_EMAIL_ID, TICKET_EMAIL_PASSWORD
from models.user_model import find_user_by_mobile
from models.ticket_model import get_assigned_tickets_by_email, add_ticket_to_queue, get_all_tickets, update_ticket
from models.account_model import get_account_by_aadhar
from models.support_emp_model import add_employees, get_least_loaded_employee, get_all_employees , get_employee_by_email

ticketing = Blueprint("ticketing", __name__)

with open("support.json", 'r') as f:
    support = json.load(f)

queues = {}
next_assignment = 0
ticket_id = 0


@ticketing.route('/login', methods=['POST'])
def login():
    data = request.json
    required_fields = ["email"]
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    email = data["email"]

    # Check if email exists in MongoDB
    employee = get_employee_by_email(email)
    if not employee:
        return jsonify({"error": "Unauthorized: Email not found"}), 401

    return jsonify({"message": "Login successful", "user": {"name": employee["name"], "email": employee["email"]}})

# deprecated
def send_mail_to_employee(employee, content):
    """Send email with given content."""
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(TICKET_EMAIL_ID, TICKET_EMAIL_PASSWORD)

    message = f'''Dear {employee['name']},\n{content}'''
    
    s.sendmail(TICKET_EMAIL_ID, employee['email'], message)
    s.quit()

# deprecated
def assign_employee(data):
    """Assign Employee and send email."""
    global next_assignment, ticket_id
    data['ticket_id'] = ticket_id
    queues[ticket_id] = data

    employee = support[next_assignment]
    queues[ticket_id]['employee_assigned'] = employee['id']

    # send mail
    send_mail_to_employee(employee, "\n".join(f"{field.capitalize()}: {data[field]}" for field in data))

    next_assignment = (next_assignment + 1) % (len(support))
    print(next_assignment)
    ticket_id += 1
    return employee

@ticketing.route('add-ticket', methods=['POST'])
def add_ticket():
    '''
    Add a Ticket in queue and assign support employee.

    Name
    Mobile
    Email
    Category Of Ticket
    Description
    '''

    data = request.json
    required_fields = ["name","mobile", "category", "description"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    userInfo = find_user_by_mobile(data["mobile"])
    accountInfo = get_account_by_aadhar(userInfo["aadhar_number"])
    data['email'] = userInfo["email"]
    data['accountInfo'] = dict(accountInfo) if accountInfo else {}
    data['status'] = "Unresolved"
    data["assignedTo"] = get_least_loaded_employee()['email']

    add_ticket_to_queue(data)

    return jsonify({'message': 'Ticket added succesfully', 'assignedTo': data['assignedTo']})

# deprecated
@ticketing.route('resolve-ticket', methods=['POST'])
def resolve_ticket():
    """Return ticket with given ID."""
    global queues
    data = request.json
    ticket_id = data['ticket_id']
    if ticket_id in queues.keys():
        resolved = queues.pop(ticket_id)
        return {'resolved': True, 'ticket': resolved}
    else:
        return{'resolved': True, 'error': 'No such ticket exists'}

@ticketing.route('get-all-tickets', methods=['GET'])
def get_all_tickets_admin():
    """Return all open tickets."""
    tickets = []
    for ticket in get_all_tickets():
        ticket['_id'] = str(ticket['_id'])
        tickets.append(ticket) 
    print(tickets)
    return jsonify({"tickets": tickets})

@ticketing.route('get-assigned-tickets', methods=['POST'])
def get_assigned_tickets():
    data = request.json
    if not "email" in data:
        return jsonify({"message": "Email is required."})

    tickets = []
    for ticket in get_assigned_tickets_by_email(data['email']):
        ticket['_id'] = str(ticket['_id'])
        tickets.append(ticket) 

    return jsonify({"email": data["email"], "tickets": tickets})

@ticketing.route('update-ticket-status', methods=['POST'])
def update_ticket_by_id():
    data = request.json

    required_fields = ["_id","status"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    print(update_ticket(data['_id'], data['status']))

    return {'message': "Updated Status Successfully"}

@ticketing.route('add-support-employees', methods=['POST'])
def add_support_employees():
    data = request.json

    if not "employees" in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    employees = []
    for employee in data['employees']:
        employee['ticket_count'] = 0
        employees.append(employee)

    add_employees(employees)

    return {"message": "Successful"}

@ticketing.route('get-all-support-employees', methods=['GET'])
def get_all_support_employees():
    """Return all support employees."""
    tickets = []
    for ticket in get_all_employees():
        ticket['_id'] = str(ticket['_id'])
        tickets.append(ticket) 
    print(tickets)
    return jsonify({"employees": tickets})