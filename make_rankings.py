import pandas as pd

def make_rankings(csv_file):
    """
    Creates speedrun rankings from a csv file with data.
    Use gather_speedrun.py to get data from https://mhwleaderboards.com/ in the proper format.
    """

    #Import data as a dataframe
    freestyle = pd.read_csv('speedrun_data.csv')

    # Filter out 'repeat runs'
    # 'Repeat run': run on the same monster, same quest, by the same runner with the same weapon, but different times.
    # Keep only the fastest run
    freestyle = freestyle.drop_duplicates(['Monster Name','Quest','Runner','Weapon'],keep='first') #Already sorted by time,
                                                                                                #first time = fastest!


    #Function to convert the time field to seconds
    def to_seconds(time_string):
        
        #Get minutes, seconds and centi seconds from string
        minutes = int(time_string[0:2])
        seconds = int(time_string[3:5])
        cents = int(time_string[6:])
        
        #Return total in seconds
        return 60*minutes+seconds+cents/100
        
    #Add Time (s) column (ie time in seconds)
    freestyle.insert(5, 'Time (s)', freestyle['Time'].apply(to_seconds))

    #Convert Star Rating to string (discrete values!)
    freestyle['Star Rating']=freestyle['Star Rating'].apply(str)



    #Abbreviate weapon names
    weapon_dict = {'Great Sword':'GS',
                'Long Sword':'LS',
                'Sword And Shield':'SnS',
                'Dual Blades':'DB',
                'Lance':'Lance',
                'Gunlance':'GL',
                'Hammer':'Hammer',
                'Hunting Horn':'HH',
                'Switch Axe':'SA',
                'Charge Blade':'CB',
                'Insect Glaive':'IG',
                'Heavy Bowgun':'HBG',
                'Light Bowgun':'LBG',
                'Bow':'Bow'    
                }

    #Apply dict to weapons column
    freestyle['Weapon']=freestyle['Weapon'].apply(lambda x: weapon_dict[x])

    # Sort dataframe by, in order: Star Rating, Monster Name, Quest, and Time
    freestyle = freestyle.sort_values(['Star Rating','Monster Name','Time (s)','Quest'],ascending=[False,True,True,True])

    #Fix indexes
    freestyle = freestyle.reset_index(drop=True)


    # Function to generate rankings by quest or monster
    def general_rank(speed_df,rank_by_column='Quest',time_column='Time (s)',sort=True):
        

        # Sort dataframe accordingly
        if sort:
            speed_df = speed_df.sort_values([rank_by_column,time_column],ascending=True)
        
        #Start with an empty list
        ranking=[]
        
        #Get a list of all items to iterate through
        rank_by_list = speed_df[rank_by_column].unique()
        
        #Iterate through all quests or monsters
        for item in rank_by_list: 
            #First entry is always rank 1
            rank = 1; 

            #Get slice of the input df corresponding to the quest name
            df_slice = speed_df[speed_df[rank_by_column]==item]

            #Append rankings to the list, for the length of the slice
            for index, row in df_slice.iterrows():
                ranking.append(rank)
                rank += 1

            #Reset rank count for next iteration
            rank=1;
        
        #Create DataFrame to return
        rank_df = pd.DataFrame(data=ranking,index=speed_df.index)
        
        #If sorted previously, return to old sorting before returning
        if sort:
            rank_df = rank_df.sort_index()

        return rank_df


    # Function to generate rankings by quest or monster, separating each weapon
    def weapon_rank(speed_df,rank_by_column='Quest',weapon_column='Weapon',time_column='Time (s)',sort=True):
        
        #Sort dataframe accordingly
        if sort:
            speed_df = speed_df.sort_values([rank_by_column,weapon_column,time_column],ascending=[True,True,True])
        
        #Start with empty list
        ranking=[] 
        
        #Get a list of all items to iterate through
        rank_by_list = speed_df[rank_by_column].unique()
        
        #Iterate through all quests or monsters
        for item in rank_by_list: 
            
            #Get slice of the input df corresponding to the quest name
            df_slice = speed_df[speed_df[rank_by_column]==item]
        
            #Get list of weapons with an entry for this quest/monster
            weapon_list = df_slice[weapon_column].unique()

            #Iterate through all weapons
            for weapon in weapon_list:
                #First entry is always rank 1
                rank = 1;     

                #Get subslice of slice_df corresponding to this weapon
                df_subslice = df_slice[df_slice[weapon_column]==weapon]

                #Append rankings to the list, for the length of the slice
                for subindex, subrow in df_subslice.iterrows():
                    ranking.append(rank)
                    rank += 1

                #Reset rank count for next iteration
                rank=1;
        
        #Create DataFrame to return
        rank_df = pd.DataFrame(data=ranking,index=speed_df.index)
        
        #If sorted previously, return to old sorting before returning
        if sort:
            rank_df = rank_df.sort_index()

        return rank_df


    # Separate TA runs. Note that Freestyle runs also encompass TA runs (ie a TA run is also a Freestyle run, but a Freestyle run
    # not be a TA run)
    ta = freestyle[freestyle['Ruleset']=='TA Rules'].copy()
    ta = ta.drop('Ruleset',axis=1) #Drop Ruleset column as it is redundant



    #Rank by monster
    freestyle['Monster/General'] = general_rank(freestyle[['Monster Name','Time (s)']],rank_by_column='Monster Name')
    ta['Monster/General'] = general_rank(ta[['Monster Name','Time (s)']],rank_by_column='Monster Name')

    #Rank by quest
    freestyle['Quest/General'] = general_rank(freestyle[['Quest','Time (s)']],rank_by_column='Quest')
    ta['Quest/General'] = general_rank(ta[['Quest','Time (s)']],rank_by_column='Quest')



    #Rank by monster and weapon type
    freestyle['Monster/Weapon'] = weapon_rank(freestyle[['Monster Name','Weapon','Time (s)']],
                                            rank_by_column='Monster Name',weapon_column='Weapon')
    ta['Monster/Weapon'] = weapon_rank(ta[['Monster Name','Weapon','Time (s)']],
                                            rank_by_column='Monster Name',weapon_column='Weapon')

    #Rank by quest and weapon type
    freestyle['Quest/Weapon'] = weapon_rank(freestyle[['Quest','Weapon','Time (s)']],
                                            rank_by_column='Quest',weapon_column='Weapon')
    ta['Quest/Weapon'] = weapon_rank(ta[['Quest','Weapon','Time (s)']],
                                            rank_by_column='Quest',weapon_column='Weapon')

    #Return the freestyle and TA dataframes
    return (freestyle,ta)


def pick_top_run(speed_df,rank_by_column='Monster/Weapon',top_pos=1):
    """
    Returns a dataframe with only the 'top_pos' best runs from
    'speed_df', as ranked by the 'rank_by_column' column.
    """

    return speed_df[speed_df[rank_by_column]==top_pos]







