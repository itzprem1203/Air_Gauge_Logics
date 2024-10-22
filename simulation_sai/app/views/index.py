import json
from django.shortcuts import render



def index(request):
    from app.models import UserLogin 
    if request.method == 'GET':
        # Query all UserLogin entries
        user_logins = UserLogin.objects.all()
        
        # Convert the queryset to a list of dictionaries
        user_logins_list = list(user_logins.values())
        
        # Serialize the list to JSON
        user_logins_json = json.dumps(user_logins_list)
        
        # Pass the serialized JSON data to the template
        context = {'user_logins_json': user_logins_json}
        print("context:",context)
        return render(request, 'app/index.html', context)

