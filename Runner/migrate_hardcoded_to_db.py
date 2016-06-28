# Compare params derived from Hardcoded and Database
# We'll make sure everything in the Hardcoded is also in the Database
# We'll print CONFIRMED if the param in Hardcoded == param in Database
# We'll pass without error if it is not in Hardcoded and it is
# None or (None, None) in the Database
# The (None, None) edge case is due to the fact that tuples are stored
# in the Database

1/0 # Don't use this anymore

import ParamLookups
import runner.models

DO_UPDATE = True

model_l = [
    runner.models.Box, 
    runner.models.Board,
    runner.models.Mouse,
]
hc_func_l = [
    ParamLookups.Hardcoded.get_box_parameters,
    ParamLookups.Hardcoded.get_board_parameters,
    ParamLookups.Hardcoded.get_mouse_parameters,
]
db_func_l = [
    ParamLookups.Database.get_box_parameters,
    ParamLookups.Database.get_board_parameters,
    ParamLookups.Database.get_mouse_parameters,
]

# Iterate through models to migrate
for model, hc_func, db_func in zip(model_l, hc_func_l, db_func_l):
    # Iterate through instances of each model and compare the params
    # recovered from the db vs from Hardcoded 
    print "MODEL %r" % model
    for obj in model.objects.all():
        print obj.name

        # Get parameters from database
        db_params = db_func(obj.name)

        # Get Hardcoded params
        try:
            hc_params = hc_func(obj.name)
        except ValueError:
            print "no hardcoded parameters found, delete this obj?"
            continue
        
        # Identify any hardcoded params that do not exist in the database
        not_in_db = [k for k, v in hc_params.items() if k not in db_params]
        if len(not_in_db) > 0:
            print "NOT IN DB: " + ' '.join(not_in_db)
        else:
            print "CONFIRMED ALL IN DB"

        # Compare each param type
        for typ, typ_db_params in db_params.items():
            typ_hc_params = hc_params[typ]
            
            # Compare each individual param
            for k, db_v in typ_db_params.items():
                # Extract hardcoded param if it exists
                # We will assume None if it's not listed in hardcoded param
                hc_v = typ_hc_params.get(k, None)
                
                if hc_v == db_v:
                    # They are the same
                    print "CONFIRMED: %s-%s-%s == %s" % (
                        typ, k, type(db_v), hc_v)
                elif hc_v is None and db_v == (None, None):
                    # edge case
                    print "CONFIRMED: %s-%s-%s == %s [hc] vs %s [db]" % (
                        typ, k, type(db_v), hc_v, db_v)
                else:
                    print "DIFFERS: %s-%s-%s == %s [hc] vs %s [db]" % (
                        typ, k, type(hc_v), hc_v, db_v)
                    
                    if DO_UPDATE:
                        print "SET %s %s" % (k, hc_v)
                        obj.__setattr__(k, hc_v)
                        obj.save()
    
    print
