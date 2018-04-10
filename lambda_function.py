import urllib2
import urllib
import json

API_BASE="http://f6caa5cd.ngrok.io"

def lambda_handler(event, context):

    if event["session"]["new"]:
        on_session_started({"requestId": event["request"]["requestId"]}, event["session"])

    if event["request"]["type"] == "LaunchRequest":
        return on_launch(event["request"], event["session"])
    elif event["request"]["type"] == "IntentRequest":
        return on_intent(event["request"], event["session"])
    elif event["request"]["type"] == "SessionEndedRequest":
        return on_session_ended(event["request"], event["session"])

def on_session_started(session_started_request, session):
    print "Starting new session."

def on_launch(launch_request, session):
    return get_welcome_response()

def on_intent(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]
    dialogState = intent_request["dialogState"]

    if intent_name == "AccountSearch":
        return get_account_search(intent)
    elif intent_name == "AccountBalance":
        return get_account_balance(intent, session)
    elif intent_name == "TransactionSearch":
        return get_transaction_search(intent,session)
    elif intent_name == "TicketAssignedTo":
        return get_ticket_assigned_to(intent,session)
    elif intent_name == "TicketRequestBy":
        return get_ticket_raised_by(intent,session)
    elif intent_name == "CreateTicket":
        return create_ticket(intent,session,dialogState)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
    print "Ending session."
    # Cleanup goes here...

def handle_session_end_request():
    card_title = "Cash Guy - Thanks"
    speech_output = "Thank you for using the Alexa Cash Guy skill.  See you next time!"
    should_end_session = True

    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))

def get_welcome_response():
    session_attributes = {}
    card_title = "Cash Guy"
    speech_output = "Welcome to the SEI Cash Guy skill. " \
                    "You can ask me for account information, transaction information or " \
                    "ask me for incident status."
    reprompt_text = "You can ask me for incident status, " \
                    "for example Get incident status."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_account_search(intent):
    session_attributes = {}
    card_title = "Account details"
    reprompt_text = ""
    should_end_session = False
    
    accountname =  intent["slots"]["accountName"]["value"]
    
    response = urllib2.urlopen(API_BASE + "/account/"+accountname.lower())
    account_details = json.load(response)   
 
    
    speech_output = "<speak>Account " + account_details["account_name"] + " is an " + account_details["account_type"] +\
    ". Account status is " + account_details["account_status"] +". Do you need to know the account balance ?</speak>"

    card_output = "Account " + account_details["account_name"] + " is an " + account_details["account_type"] +\
    ". Account status is " + account_details["account_status"] + "."
    
    reprompt_text = "Do you need to know the account balance ?"
    
    session_attributes["account_details"] = account_details   

    return build_response(session_attributes, build_ssml_speechlet_response(
        card_title, speech_output,card_output, reprompt_text, should_end_session))


def get_account_balance(intent,session):
    session_attributes = {}
    card_title = "Account balance"
    reprompt_text = ""
    should_end_session = False
    
    if session["attributes"]["account_details"] is not None:
        account_details = session["attributes"]["account_details"]
        
    speech_output = "<speak>Account balance of "+ account_details["account_name"] + " is <say-as interpret-as='cardinal'>" + account_details["account_balance"] +"</say-as></speak>"

    card_output = "Account balance of "+ account_details["account_name"] + " is " + account_details["account_balance"] +"."
    
    reprompt_text = ""

    return build_response(session_attributes, build_ssml_speechlet_response(
        card_title, speech_output,card_output, reprompt_text, should_end_session))


def get_transaction_search(intent,session):
    session_attributes = {}
    card_title = "Transaction Search"
    reprompt_text = ""
    should_end_session = False
    
    if "attributes" in session: 
        if session["attributes"]["account_details"] is not None:
            account_details = session["attributes"]["account_details"]
            accountId = account_details["account_id"]
    else:
        accountId=0
    
    transaction_type = intent["slots"]["transactionType"]["value"]
    data = urllib.urlencode({'account_id'  : accountId})
    url = API_BASE + "/transaction/"+ transaction_type.lower()
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    transaction_details = json.load(response)      
    if "message" in transaction_details:
        speech_output = "Sorry. No " + transaction_type + " transactions found."
        card_output = "Sorry. No " + transaction_type + " transactions found."
    else:
        l_count = len(transaction_details)
        detail = ""
        strAnd = ""
        multiword = " are "
        if l_count ==1:
            multiword = " is " 
            
        for json_txn in transaction_details:
            detail = detail + strAnd + " Transaction of " + str(json_txn["transaction_qty"]) + " quantities of " + json_txn["instrument_name"] +" . "
        speech_output = "There" + multiword + str(l_count) + transaction_type + " transactions. " + detail
        card_output = "There " + multiword + str(l_count) + transaction_type + " transactions. " + detail
    
    reprompt_text = ""

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
    
def get_ticket_assigned_to(intent,session):
    session_attributes = {}
    card_title = "Ticket details"
    reprompt_text = ""
    should_end_session = False
    
    assignedTo =  intent["slots"]["assignedTo"]["value"]
    
    response = urllib2.urlopen(API_BASE + "/ticket/"+assignedTo.lower())
    ticket_details = json.load(response)   
    l_count = len(ticket_details)
    multiword = " are "
    if l_count ==1:
        multiword = " is "
    
    count_detail = "There" + multiword + str(l_count) + " tickets assigned to " + assignedTo + " ."
    ticket_detail = ""
    for json_txn in ticket_details:
        ticket_detail = ticket_detail + json_txn["priotity"] \
        + " ticket raised by " + json_txn["requestor"] + " is in " + json_txn["ticket_status"] +\
        " status . "
    
    speech_output = "<speak>" + count_detail + ticket_detail + " Do you need more ticket details ?</speak>"

    card_output = count_detail + ticket_detail + " Do you need more ticket details ?"
    
    reprompt_text = "Do you need more ticket details ?"
    
    session_attributes["ticket_details"] = ticket_details   

    return build_response(session_attributes, build_ssml_speechlet_response(
        card_title, speech_output,card_output, reprompt_text, should_end_session))

def get_ticket_raised_by(intent,session):
    session_attributes = {}
    card_title = "Ticket details"
    reprompt_text = ""
    should_end_session = False
    
    requestedBy =  intent["slots"]["requestedBy"]["value"]
    
    response = urllib2.urlopen(API_BASE + "/ticketby/"+requestedBy.lower())
    ticket_details = json.load(response)   
    l_count = len(ticket_details)
    multiword = " are "
    if l_count ==1:
        multiword = " is "
    
    count_detail = "There"+ multiword + str(l_count) + " tickets requested by " + requestedBy + " ."
    ticket_detail = ""
    for json_txn in ticket_details:
        ticket_detail = ticket_detail + json_txn["priotity"] \
        + " ticket assigned to " + json_txn["assigned_to"] + " is in " + json_txn["ticket_status"] +\
        " status . "
    
    speech_output = "<speak>" + count_detail + ticket_detail + " Do you need more ticket details ?</speak>"

    card_output = count_detail + ticket_detail + " Do you need more ticket details ?"
    
    reprompt_text = "Do you need more ticket details ?"
    
    session_attributes["ticket_details"] = ticket_details   

    return build_response(session_attributes, build_ssml_speechlet_response(
        card_title, speech_output,card_output, reprompt_text, should_end_session))

def create_ticket(intent,session,dialogSate):
    status = intent["confirmationStatus"]
    if status == "CONFIRMED":
        return insert_ticket(intent,session,dialogSate)
    elif dialogSate in ("STARTED", "IN_PROGRESS"):
        return continue_dialog()
    
def continue_dialog():
    message = {}
    session_attributes = {}
    message['shouldEndSession'] = False
    message['directives'] = [{'type': 'Dialog.Delegate'}]
    return build_response(session_attributes,message)

def insert_ticket(intent,session,dialogSate):
    card_title = "Create ticket"
    should_end_session = False
    session_attributes = {}
    category = intent["slots"]["category"]["value"]
    priority = intent["slots"]["priority"]["value"]
    description = intent["slots"]["description"]["value"]
    data = urllib.urlencode({'ticket_category'  : category,
                             'priotity'  : priority,
                             'ticket_description'  : description})
    url = API_BASE + "/ticketby/Alex"
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    transaction_details = json.load(response)
    speech_output = "<speak>Ticket is created</speak>"
    card_output = "Ticket is created"   
    reprompt_text = ""
    return build_response(session_attributes, build_ssml_speechlet_response(
        card_title, speech_output,card_output, reprompt_text, should_end_session))
    
    
def get_system_status():
    session_attributes = {}
    card_title = "BART System Status"
    reprompt_text = ""
    should_end_session = False

    response = urllib2.urlopen(API_BASE + "/status")
    bart_system_status = json.load(response)   

    speech_output = "There are currently " + bart_system_status["traincount"] + " trains operating. "

    if len(bart_system_status["message"]) > 0:
        speech_output += bart_system_status["message"]
    else:
        speech_output += "The trains are running normally."

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_elevator_status():
    session_attributes = {}
    card_title = "BART Elevator Status"
    reprompt_text = ""
    should_end_session = False

    response = urllib2.urlopen(API_BASE + "/elevatorstatus")
    bart_elevator_status = json.load(response) 

    speech_output = "BART elevator status. " + bart_elevator_status["bsa"]["description"]

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_train_times(intent):
    session_attributes = {}
    card_title = "BART Departures"
    speech_output = "I'm not sure which station you wanted train times for. " \
                    "Please try again."
    reprompt_text = "I'm not sure which station you wanted train times for. " \
                    "Try asking about Fremont or Powell Street for example."
    should_end_session = False

    if "Station" in intent["slots"]:
        station_name = intent["slots"]["Station"]["value"]
        station_code = get_station_code(station_name.lower())

        if (station_code != "unkn"):
            card_title = "BART Departures from " + station_name.title()

            response = urllib2.urlopen(API_BASE + "/departures/" + station_code)
            station_departures = json.load(response)   

            speech_output = "Train departures from " + station_name + " are as follows: "
            for destination in station_departures["etd"]:
                speech_output += "Towards " + destination["destination"] + " on platform " + destination["estimate"][0]["platform"] + ". ";
                for estimate in destination["estimate"]:
                    if estimate["minutes"] == "Leaving":
                        speech_output += "Leaving now: "
                    elif estimate["minutes"] == "1":
                        speech_output += "In one minute: "
                    else:
                        speech_output += "In " + estimate["minutes"] + " minutes: "

                    speech_output += estimate["length"] + " car train. "

            reprompt_text = ""

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": output
        },
        "card": {
            "type": "Simple",
            "title": title,
            "content": output
        },
        "reprompt": {
            "outputSpeech": {
                "type": "PlainText",
                "text": reprompt_text
            }
        },
        "shouldEndSession": should_end_session
    }

def build_ssml_speechlet_response(title, output, card_output, reprompt_text, should_end_session):
    return {
        "outputSpeech": {
            "type": "SSML",
            "ssml": output
        },
        "card": {
            "type": "Simple",
            "title": title,
            "content": card_output
        },
        "reprompt": {
            "outputSpeech": {
                "type": "PlainText",
                "text": reprompt_text
            }
        },
        "shouldEndSession": should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response": speechlet_response
    }
