import json
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.messaging_response import MessagingResponse
import emoji


@csrf_exempt
def index(request):
    if request.method == 'POST':
        # Retrieve incoming message from POST request
        incoming_msg = request.POST['Body'].lower()

        # Create Twilio XML response
        resp = MessagingResponse()
        msg = resp.message()

        if incoming_msg == 'hi':
            response = emoji.emojize("""
*Hi! I am your friend when you are lonely* :wave:
You can ask me the following:

:black_small_square: *'Quote'*: To hear an inspirational quote to start your day right! :rocket:
:black_small_square: *'Cat'*: To get a cat picture :cat:
:black_small_square: *'Recipe'*: Whenever you don't have inspiration what to cook tonight :fork_and_knife:
""", use_aliases=True)
            msg.body(response)

        elif incoming_msg == 'quote':
            r = requests.get('https://api.quotable.io/random')

            if r.status_code == 200:
                data = r.json()
                quote = f'{data["content"]}, {data["author"]}'
            else:
                quote = 'I could not retrieve a quote this time, sorry.'

            msg.body(quote)

        elif incoming_msg == 'cat':
            msg.media('https://cataas.com/cat')

        elif incoming_msg.startswith('recipe'):
            search_text = incoming_msg.replace('recipe', '')
            search_text = search_text.strip()

            if len(search_text) != 0:
                data = json.dumps({'searchText': search_text})

                result = ''
                r = requests.put(
                    # Update scraper task input with the user's search text
                    'https://api.apify.com/v2/actor-tasks/FNS5hgcrbFzYL1Gyx/input?token=Sbc2XbtjJ3ceKHyo344bAvKxE',
                    data=data,
                    headers={"content-type": "application/json"})
                if r.status_code != 200:
                    result = 'Sorry, I cannot find recipes at this time. Please try again later.'

                r = requests.post(
                    # Scrape all recipes for the top 5 search results
                    'https://api.apify.com/v2/actor-tasks/FNS5hgcrbFzYL1Gyx/runs?token=Sbc2XbtjJ3ceKHyo344bAvKxE')
                if r.status_code != 201:
                    result = 'Sorry, I cannot search at Allrecipes.com at this time. Please try again later.'

                if not result:
                    result = emoji.emojize(f'I am searching Allrecipes.com for the best {search_text} recipes. :fork_and_knife:')
                    result += "\nPlease wait for a few moments before typing 'get recipe' to get your recipes!"
            else:
                result = 'What kind of ingredient(s) do you like to eat tonight?'
            msg.body(result)

        elif incoming_msg == 'get recipe':
            # get the last run details
            r = requests.get('https://api.apify.com/v2/actor-tasks/FNS5hgcrbFzYL1Gyx/runs/last?token=Sbc2XbtjJ3ceKHyo344bAvKxE')

            if r.status_code == 200:
                data = r.json()

                # check if last run has succeeded or is still running
                if data['data']['status'] == 'RUNNING':
                    result = 'Sorry, your previous search request is still running.'
                    result += "\nPlease wait for a few moments before typing 'get recipe' to get your recipes!"

                elif data['data']['status'] == 'SUCCEEDED':

                    # get the last run dataset items
                    r = requests.get(
                        'https://api.apify.com/v2/actor-tasks/FNS5hgcrbFzYL1Gyx/runs/last/dataset/items?token=Sbc2XbtjJ3ceKHyo344bAvKxE')
                    data = r.json()

                    if data:
                        result = ''

                        for recipe_data in data:
                            url = recipe_data['url']
                            name = recipe_data['name']
                            rating = recipe_data['rating']
                            rating_count = recipe_data['ratingcount']
                            prep = recipe_data['prep']
                            cook = recipe_data['cook']
                            ready_in = recipe_data['ready in']
                            calories = recipe_data['calories']

                            result += """
                            *{}*
                            _{} calories_
                            Rating: {:.2f} ({} ratings)
                            Prep: {}
                            Cook: {}
                            Ready in: {}
                            Recipe: {}
                            """.format(
                                name, calories, float(rating), rating_count, prep, cook, ready_in, url)
                    else:
                        result = f'Sorry, I could not find any results for {search_text}'
                else:
                    result = 'Sorry, your previous search query has failed. Please try searching again.'
            else:
                result = 'I cannot retrieve recipes at this time. Sorry!'

            msg.body(result)
        return HttpResponse(str(resp))
