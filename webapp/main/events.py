from time import time
from flask import session
from flask_socketio import emit, join_room, leave_room,send
from .. import socketio
from .. import secAIAssistant

@socketio.on('prompt', namespace='/secai')  
def run_prompt(user_prompt):  
    print('Received message: ' + user_prompt)  
    processed_responses=secAIAssistant.run_prompt('html',user_prompt,emit)
    emit('completedmessage',{"message":'Processing Done'})
@socketio.on('clear_session', namespace='/secai')  
def clear_session(clear):  
    print('Received message: Clear Session' )  
    processed_responses=secAIAssistant.clear_session()
    emit('debugmessage',{"message":'Session cleared'})