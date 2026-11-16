from django.shortcuts import render, redirect
from .models import GameState

def game_view(request):
    game, created = GameState.objects.get_or_create(id=1)
    error_message = None

    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == 'give_up':
            game.is_over = True
            game.save()
            
        elif action == 'send_city':
            city = request.POST.get('city', '').strip()
            city_lower = city.lower()
            
            if city:
                
                if city_lower in [c.lower() for c in game.used_cities_list]:
                    error_message = "Этот город уже называли!"
                    
                elif game.last_city:
                    last_letter = game.last_city[-1].lower()
                    if last_letter in ['ъ', 'ы', 'ь'] and len(game.last_city) > 1:
                        last_letter = game.last_city[-2].lower()
                    
                    if city_lower[0] != last_letter:
                        error_message = f"Город должен начинаться на '{last_letter.upper()}'!"
                
                if not error_message:
                    cities = game.used_cities_list
                    cities.append(city)
                    game.used_cities = ",".join(cities)
                    
                    game.last_city = city
                    game.current_turn = 2 if game.current_turn == 1 else 1
                    game.save()
                    return redirect('game') 

    cities_list = game.used_cities_list
    
    context = {
        'game': game,
        'cities': cities_list,
        'error': error_message,
    }
    return render(request, 'index.html', context)
