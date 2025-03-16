from flask import Blueprint, request, jsonify
import json, smtplib
from config import TICKET_EMAIL_ID, TICKET_EMAIL_PASSWORD

ticketing = Blueprint("ticketing", __name__)

with open("support.json", 'r') as f:
    support = json.load(f)

queues = {}
next_assignment = 0
ticket_id = 0

def send_mail_to_employee(employee, content):
    """Send email with given content."""
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(TICKET_EMAIL_ID, TICKET_EMAIL_PASSWORD)

    message = f'''Dear {employee['name']},\n{content}'''
    
    s.sendmail(TICKET_EMAIL_ID, employee['email'], message)
    s.quit()

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

@ticketing.route('/add-ticket', methods=['POST'])
def add_ticket():
    '''
    Add a Ticket in queue and assign support employee.

    Name
    Number
    Email
    Category Of Ticket
    Description
    '''

    data = request.json
    employee = assign_employee(data)
    return {'data': data, 'employee': employee}


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
def get_all_tickets():
    """Return all open tickets."""
    global queues
    return queues