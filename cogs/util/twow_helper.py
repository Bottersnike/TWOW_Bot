import re
import random

RESPONSES_PER_SLIDE = 10

def new_twow(db, identifier, channel, owner):
    s = {}
    s['owner'] = owner
    s['round'] = 1
    s['season'] = 1
    s['voting'] = False
    s['seasons'] = {'season-1':
                    {'rounds':
                        {'round-1':
                        {
                        'alive':[],
                        'prompt': None,
                        'responses': {},
                        'slides': {},
                        'votes': [],
                        }
                        }
                    }
                    }
    
    db.server_data[channel] = s
    db.servers[channel] = identifier
    db.save_data()
    
def respond(db, id, responder, response): # 1 = no twow, 3 = voting started, 5 = no prompt, 7 = dead, 9 = too many words
    s_ids = {i[1]:i[0] for i in db.servers.items()}
    if id not in s_ids:
        return (1, '')
    
    sd = db.server_data[s_ids[id]]
    
    if sd['voting']:
        return (3, '')
    
    if 'season-{}'.format(sd['season']) not in sd['seasons']:
        sd['seasons']['season-{}'.format(sd['season'])] = {}
    if 'round-{}'.format(sd['round']) not in sd['seasons']['season-{}'.format(sd['season'])]['rounds']:
        sd['seasons']['season-{}'.format(sd['season'])]['rounds']['round-{}'.format(sd['round'])] = {'prompt': None, 'responses': {}, 'slides': {}, 'votes': []}
    
    round = sd['seasons']['season-{}'.format(sd['season'])]['rounds']['round-{}'.format(sd['round'])]
    
    if round['prompt'] is None:
        return (5, '')

    if sd['round'] > 1 and responder not in round['alive']:
        return (7, '')
    elif sd['round'] == 1 and responder not in round['alive']:
        round['alive'].append(responder)
        
    success = 0
    if responder in round['responses']:
        success += 2
    if len(response.split(' ')) > 10:
        success += 4
    if len(response) > 140:
        return (9, '')
    
    changed = False
    with open('banned_words.txt') as bw:
        banned_w = bw.read().split('\n')
    for i in banned_w:
        if i:
            pattern = re.compile(i, re.IGNORECASE)
            if pattern.match(response):
                response = pattern.sub('\\*' * len(i), response)
                print(response)
                changed = True
    if changed:
        success += 8
    
    round['responses'][responder] = response.encode('utf-8')
    db.save_data()
    return success, response

def create_slides(db, round, voter):
# Sort all responses based off their number of votes
    responses = [[i, 0] for i in round['responses']]
    for i in responses:
        if i[0] == voter:
            responses.remove(i)
    for vote in round['votes']:
        # Each vote is a list of user IDs going from best to worst
        for i in vote['vote']:
            for r in responses:
                if r[0] == i:
                    r[1] += 1
                    break
            else:
                if i != voter:
                    responses.append([i, 1])
    responses.sort(key=lambda x:x[1])

    if len(responses) < 2:
        return False
    
    # ~~Calculate the nubmer of responses per slide~~ Global at start of file.
    # Take that many items from the list of responses.
    
    slide = responses[:RESPONSES_PER_SLIDE]
    slide = [i[0] for i in slide]
    random.shuffle(slide)
    
    # Save as a slide.
    round['slides'][voter] = slide
    
    db.save_data()
    return True