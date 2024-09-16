def register_routes():
    routes = [
        ('/create_opportunity', 'POST', create_opportunity, 'opportunity'),
        ('/available_slots', 'GET', available_slots, 'slots'),
        ('/events', 'GET', get_events, 'events'),
        ('/free_slots', 'GET', free_slots, 'free_slots')  
    ]
    
    for route, method, func, endpoint in routes:
        if endpoint == 'free_slots':
            # Para free_slots solo se pasan 4 argumentos
            app.add_url_rule(
                route, 
                view_func=lambda func=func: func(models, db, uid, password), 
                methods=[method], 
                endpoint=endpoint
            )
        else:
            # Para los demás se pasan 5 argumentos
            app.add_url_rule(
                route, 
                view_func=lambda func=func: func(models, db, uid, password, mexico_tz), 
                methods=[method], 
                endpoint=endpoint
            )

register_routes()
