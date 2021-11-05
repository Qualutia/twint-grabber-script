import twint, numpy, datetime
from sys import argv
import re
import pandas as pd
from textblob import TextBlob
import re
from textblob import Blobber
import nltk
from nltk.corpus import stopwords
from collections import Counter
from textblob.sentiments import NaiveBayesAnalyzer



# //------/ Setup / ------// #

# Area of search
anl_name = "Market Area"
grab_type = 'geo' 

name = 'princesfound'

# lon = [0.008357627539407034]
# lat = [51.50797091169211]
# rad = [0.125]



# Expressed as : [[latitude,longitude,radius], [latitude,longitude,radius]]

areas = []

# for i in range(len(lon)):
#     area = str(lat[i]) + ',' +  str(lon[i]) + ',' + str(rad[i]) + 'km' 
#     areas.append(area)


# Expressed as : %YYYY-%MM-%DD
since    = '2012-01-01'
until    = '2021-01-31'

# //------/ Setup [End] / ------// #



# //------/ Grab unique usernames from geolocation / ------// #
# Grabs the unique usernames from the provided areas in a specified timeframe

frames = []

def grabUsernames(geo):

    c = twint.Config()
    c.Replies = True
    c.Retweets = True
    c.Search = "lang:en"
    c.Geo = geo
    c.Since = since
    c.Until = until
    c.Pandas = True
    c.Hide_output = True
    twint.run.Search(c)

    Tweets_df = twint.storage.panda.Tweets_df

    frames.append(Tweets_df)


# Grabs all the users from the areas
usernames = [name]

# for area in areas:    
#     users = grabUsernames(area)




# usernames = pd.concat(frames)['username'].values

# Grabs only unique values from array
# usernames = list(dict.fromkeys(usernames))

# //------/ Grab Users [End] / ------// #


# //------/ Grab all relevant user tweets / ------// #

def grabUser(username):
    c = twint.Config()

    c.Custom['tweet']   = ["id", "user_id", "username", "place", "tweet", "mentions", "replies_count", "retweets_count", "likes_count", "hashtags", "user_rt", "reply_to", "language" ]
    c.Replies           = True
    c.Retweets          = False
    c.Hide_output       = True
    c.Search            = "lang:en"
    c.Username          = username
    c.Limit             = 2
    c.Store_pandas      = True
    c.Pandas            = True
    c.Since             = since
    c.Until             = until

    twint.run.Search(c)

    Tweets_df = twint.storage.panda.Tweets_df


    # user_tweets = twint.output.tweets_list
    return Tweets_df




# //------/ Write the JSON file / ------// #

file = open("./data/grab_data.json", "w", encoding="utf-8")
file.write("{" + "\n")

file.write('\t"info": {"name": ' + '"' + anl_name + '"' + ', "type": "' + grab_type + '" ,"geo": [')

for index,area in enumerate(areas):
    if index + 1 == len(areas):
        file.write('{"lat": ' + str(lat[index]) + ', "lon": ' + str(lon[index]) + ', "radius": ' + str(rad[index]) + '}]')
    else:
        file.write('{"lat": ' + str(lat[index]) + ', "lon": ' + str(lon[index]) + ', "radius": ' + str(rad[index]) + '},')

file.write(', "since": "' + since + '" , "until": "' + until + '"},\n\t"users": [ \n')

# Generate the user profile
for i in range(len(usernames)) :


    user_tweets = grabUser(usernames[i])
    

    # if user_tweets['place'][0] :
    #     place = str(user_tweets.at[0, 'place']['coordinates'])
    # else:
    place = "[]"

    # print(user_tweets['place'].values[0])

    #Sentiment Analysis

    dict_hashtags_polarity          = {}
    dict_hashtags_occurence         = {}
    dict_hashtags_subjectivity         = {}
    dict_links_polarity             = {}
    dict_links_subjectivity         = {}
    dict_links_occurence            = {}
    

    dict_links_naive_pos         = {}
    dict_links_naive_neg         = {}

    dict_hashtags_naive_pos      = {}
    dict_hashtags_naive_neg      = {}

    general_nba_pos = 0
    general_nba_neg = 0
    
    count_positive                  = 0
    count_negative                  = 0
    count_neutral                   = 0

    generalPolarity                 = 0
    generalSubjectivity             = 0
    tweet_analysis_count            = 0
    likes_analysis_count            = 0
    replies_analysis_count          = 0

    tb = Blobber(analyzer=NaiveBayesAnalyzer())

    print('-------------')
    try:
        for count, tweet in enumerate(user_tweets['tweet']):
            
            
            # print(tweet)


            # //---/ Links /---// #
            # Find mentions in specific tweet
            tweetMentions_temp  = re.findall("@(\w{1,15})", tweet)
            # print(user_tweets['reply_to'][count])
            
            # print(user_tweets['reply_to'][count][0])
            if user_tweets['reply_to'][count]:
                tweetReplyTo_temp   = user_tweets['reply_to'][count][0]['screen_name']
                tweetReplyTo_temp   = [tweetReplyTo_temp]   #force list
            
            
            
            # Sentence value
            sentence_temp       = tweet.replace('@', '')
            blob                = TextBlob(sentence_temp)
            
            blob_naive          = tb(sentence_temp)

            naive_positive = blob_naive.sentiment.p_pos
            naive_negative = blob_naive.sentiment.p_neg

            general_nba_neg = (general_nba_neg + naive_negative) / 2
            general_nba_pos = (general_nba_pos + naive_positive) / 2

            # Add to the general analysis
            generalPolarity     = (generalPolarity + blob.sentiment.polarity) / 2
            generalSubjectivity = (generalSubjectivity + blob.sentiment.subjectivity) / 2 


            # print(blob.sentiment)

            # print(blob_naive.sentiment)

            if blob.sentiment.polarity > 0:
                count_positive += 1
            elif blob.sentiment.polarity < 0:
                count_negative += 1
            else:
                count_neutral += 1

            tweet_analysis_count = tweet_analysis_count + 1

            likes_analysis_count = likes_analysis_count + user_tweets['nlikes'][count]
            replies_analysis_count = replies_analysis_count + user_tweets['nreplies'][count]



        

            #for HASHTAGS
            for hashtag in user_tweets['hashtags'][count]:
                
                if hashtag in dict_hashtags_occurence:
                    dict_hashtags_occurence[hashtag] = dict_hashtags_occurence[hashtag] + 1
                else:
                    dict_hashtags_occurence.update({ hashtag : 1 })

                if hashtag in dict_hashtags_polarity:
                    dict_hashtags_polarity[hashtag] = (dict_hashtags_polarity[hashtag] + blob.sentiment.polarity) / 2
                else:
                    dict_hashtags_polarity.update({ hashtag : blob.sentiment.polarity })

                if hashtag in dict_hashtags_subjectivity:
                    dict_hashtags_subjectivity[hashtag] = (dict_hashtags_subjectivity[hashtag] + blob.sentiment.subjectivity) / 2
                else:
                    dict_hashtags_subjectivity.update({ hashtag : blob.sentiment.subjectivity })


                if hashtag in dict_hashtags_naive_pos:
                    dict_hashtags_naive_pos[hashtag] = (dict_hashtags_naive_pos[hashtag] + naive_positive) / 2
                else:
                    dict_hashtags_naive_pos.update({ hashtag : naive_positive })

                if hashtag in dict_hashtags_naive_neg:
                    dict_hashtags_naive_neg[hashtag] = (dict_hashtags_naive_pos[hashtag] + naive_negative) /2
                else:
                    dict_hashtags_naive_neg.update({ hashtag : naive_negative })


                
                        


            # For mentions
            for username in tweetMentions_temp:
                if username in dict_links_polarity:
                    dict_links_polarity[username] = (dict_links_polarity[username] + blob.sentiment.polarity)  / 2
                else:
                    dict_links_polarity.update({ username : blob.sentiment.polarity })

                if username in dict_links_subjectivity:
                    dict_links_subjectivity[username] = (dict_links_subjectivity[username] + blob.sentiment.subjectivity) / 2
                else:
                    dict_links_subjectivity.update({ username : blob.sentiment.subjectivity })

                if username in dict_links_naive_pos:
                    dict_links_naive_pos[username] = (dict_links_naive_pos[username] + (naive_positive)) / 2
                else:
                    dict_links_naive_pos.update({ username : naive_positive })

                if username in dict_links_naive_neg:
                    dict_links_naive_neg[username] = (dict_links_naive_neg[username] + (naive_negative)) / 2
                else:
                    dict_links_naive_neg.update({ username : naive_negative })

            # For reply_to
            for username in tweetReplyTo_temp:

                if username in dict_links_occurence:
                    dict_links_occurence[username] = dict_links_occurence[username] + 1
                else:
                    dict_links_occurence.update({ username : 1 })

                if username in dict_links_polarity:
                    dict_links_polarity[username] = (dict_links_polarity[username] + (blob.sentiment.polarity)) / 2
                else:
                    dict_links_polarity.update({ username : (blob.sentiment.polarity) })

                if username in dict_links_subjectivity:
                    dict_links_subjectivity[username] = (dict_links_subjectivity[username] + (blob.sentiment.subjectivity)) / 2
                else:
                    dict_links_subjectivity.update({ username : blob.sentiment.subjectivity })

                if username in dict_links_naive_pos:
                    dict_links_naive_pos[username] = (dict_links_naive_pos[username] + (naive_positive)) / 2
                else:
                    dict_links_naive_pos.update({ username : naive_positive })

                if username in dict_links_naive_neg:
                    dict_links_naive_neg[username] = (dict_links_naive_neg[username] + (naive_negative)) / 2
                else:
                    dict_links_naive_neg.update({ username : naive_negative })


        user_polarity       = generalPolarity
        user_subjectivity   = generalSubjectivity


        
        # //------/ Info /------// #

        file.write( '\t\t{' + '\t\n\t\t\t"info": ' + '{"id"' + ':' + str(user_tweets['user_id'].values[0]) 
        + ', "name": ' + '"' + str(user_tweets['name'].values[0]) + '"' + ', "username": ' + '"' + str(user_tweets['username'].values[0]) + '"' + ',' + '"place"' + ':' + place 
        + ', "tweets_count": ' + '""' + ', "analysis_count": {"tweets_count": ' + str(tweet_analysis_count) + ', "likes_count": ' + str(likes_analysis_count) + ', "replies_count": ' + str(replies_analysis_count) + ', "negative_count": ' + str(count_negative) 
        + ', "uniq_hashtags_count": ' + str(len(dict_hashtags_occurence)) + ', "positive_count": ' + str(count_positive) + ', "neutral_count": ' + str(count_neutral) + '}, "potential":' + '""' + ', "polarity": ' + str(user_polarity) + ', "subjectivity": ' + str(user_subjectivity)  + ', "nba_pos": ' + str(general_nba_pos) + ', "nba_neg": ' + str(general_nba_neg)
        # + ', "profile": {' + '"openess": ' + str(user_openess) + ', "concienciousness": ' + str(user_concienciousness) + ', "extraversion": ' + str(user_extraversion) + ', "agreableness": ' + str(user_agreableness) + ', "neuroticism": ' + str(user_neuroticism) + '}'  
        + '},')


        # //------/ Hashtags /------// #

        file.write( '\n\t\t\t"hashtags": [')

        if len(dict_hashtags_occurence) > 0:

            for index in range(len(dict_hashtags_occurence)): 

                key = list(dict_hashtags_occurence)[index]

                if index + 1 == len(dict_hashtags_occurence):
                    file.write('{"username": "' + str(key) + '", "polarity": ' + str(dict_hashtags_polarity[key]) + ', "occurence": ' + str(dict_hashtags_occurence[key]) + ', "subjectivity": ' + str(dict_hashtags_subjectivity[key])  + ', "nba_pos": ' + str(dict_hashtags_naive_pos[key]) + ', "nba_neg": ' + str(dict_hashtags_naive_neg[key]) + '} ],')
                else:
                    file.write('{"username": "' + str(key) + '", "polarity": ' + str(dict_hashtags_polarity[key]) + ', "occurence": ' + str(dict_hashtags_occurence[key]) + ', "subjectivity": ' + str(dict_hashtags_subjectivity[key])  + ', "nba_pos": ' + str(dict_hashtags_naive_pos[key]) + ', "nba_neg": ' + str(dict_hashtags_naive_neg[key]) + '},')
        else:
            file.write( '],')

        print(count)
        # //------/ Links /------// #

        file.write( '\n\t\t\t"links": [')

        if len(dict_links_occurence) > 0:
            for index in range(len(dict_links_occurence)): 

                key = list(dict_links_occurence)[index]

                if index + 1 == len(dict_links_occurence):
                    file.write('{"username": "' + str(key) + '", "polarity": ' + str(dict_links_polarity[key]) + ', "occurence": ' + str(dict_links_occurence[key]) + ', "subjectivity": ' + str(dict_links_subjectivity[key]) + ', "nba_pos": ' + str(dict_links_naive_pos[key]) + ', "nba_neg": ' + str(dict_links_naive_neg[key]) + '} ]')
                else:
                    file.write('{"username": "' + str(key) + '", "polarity": ' + str(dict_links_polarity[key]) + ', "occurence": ' + str(dict_links_occurence[key]) + ', "subjectivity": ' + str(dict_links_subjectivity[key]) + ', "nba_pos": ' + str(dict_links_naive_pos[key]) + ', "nba_neg": ' + str(dict_links_naive_neg[key]) + '},')
        else:
            file.write( '],')

    except:
        print("An exception occurred at user grab function")
        print("Adding and exception in JSON")

        file.write('\n\t\tError at userGrab()')



    if len(usernames) == i + 1:
        file.write("\n\t\t}\n")
    
    else:
        file.write("\n\t\t},\n")


file.write("\t]\n}")