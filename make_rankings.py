import pandas as pd
import numpy as np
from string import ascii_uppercase

#Dictionary of weapon types
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


def make_rankings(csv_file):
    """
    Creates speedrun rankings from a csv file with data.
    Use gather_speedrun.py to get data from https://mhwleaderboards.com/ in the proper format.
    """

    #Import data as a dataframe
    try:
        freestyle = pd.read_csv(csv_file)
    except:
        print("Speedrun data not found! Try running gather_speerdrun.py first!")
        
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

    #Apply dict to weapons column to have short names
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
            rank=1
        
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
                rank=1
        
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

    #Save formatted dataframes
    freestyle.to_csv('freestyle.csv',index=False)
    ta.to_csv('ta.csv',index=False)

    #Return the freestyle and TA dataframes
    return (freestyle,ta)

def filter_by_weapon(speed_df,weapon_array=np.array([]),filter_by='Quest',weapon_column='Weapon'):
    """
    Filters out runs that don't have all the weapon types given by weapon_list.
    Filtering is done by unique groups in the 'filter_by' column.
    Defaults:
        filter_by='Quest'         --> filter speed_df to return only quests with all weapon_types
        weapon_array=np.array([]) --> if weapon_array is empty, leave only runs with ALL weapons
        weapon_columns            --> 'Weapon', name of column with weapon types
    """
    
    #Check for empty weapon_array
    if not weapon_array.size: 
    #Get array of all weapon types
        weapon_array = np.sort(np.array(speed_df[weapon_column].unique())) #Sort to compare later
    
    #Get the array to filter by
    filter_array = np.array(speed_df[filter_by].unique())

    #Start with an empty dataframe
    filter_df = pd.DataFrame() 

    for item in filter_array:

        #Get a slice of speed_df corresponding to the current item
        slice_df = speed_df[speed_df[filter_by] == item]

        #Check if the slice has all weapon types
        check = np.array_equal(weapon_array,np.sort(speed_df[speed_df[filter_by]==item][weapon_column].unique()))

        #Concatenate to filter_df, if all weapons are present
        if check:
            filter_df = pd.concat([filter_df,slice_df])

    return filter_df.reset_index(drop=True)

def average_top_runs(speed_df,rank_column,weapon_column='Weapon',time_column='Time (s)',top_pos=1):
    """
    Returns a DataFrame with the average top speedrun times for each weapon class,
    as ordered by the 'rank_column' column.
    This will take the 'top_pos' times into the average. For top_pos=1, that's
    only the fastest time, top_pos=2 means it's the fastest 2 times, etc.
    Return value is ordered by time_column, going from fastest to slowest.
    """

    #Pick out the top runs
    avg = speed_df[speed_df[rank_column]<=top_pos]

    #Group by weapon type and get the mean values
    avg = avg.groupby(weapon_column).mean().reset_index()

    #Simplify time values
    avg['Time (s)'] = avg['Time (s)'].apply(lambda x: round(x,2))

    #Sort weapons
    avg = avg.sort_values('Time (s)',ascending=True)

    #Update index to correspond to rankings (ie start at 1 rather than 0)
    avg = avg.reset_index()
    avg.index += 1

    #Return
    return avg

def make_tiers(rank_df,n_tiers=5,tier_list=[],weapon_column='Weapon (long)',time_column='Time (s)',sort=False):
    """
    Separates weapons from a ranking, given by 'rank_df' into tiers, sorted by the 'time_column'.
    Weapons will be split into 'n_tiers' tiers. Weapon list is obtained from weapon_column.
    """

    #Sort rank_df by time_column if desired
    if sort:
        rank_df = rank_df.sort_values(time_column,ascending=True)

    #If tier list is empty, create it from ascii_uppercase, with S as the first possible rank
    if not tier_list:
        tier_list = 'S'+ascii_uppercase

    #Time gap between fastest and slowest time
    t_f = rank_df[time_column].min() #Fastest time
    t_s = rank_df[time_column].max() #Slowest time
    time_gap = t_s - t_f

    #First tier will be made so the fastest time sits in the middle of it
    #and the tier list has exactly 'n_tiers' tiers
    #This expression can be derived from the following 3 equations:
    #time_gap = (t_f - t_s)              (t_f -> slowest time, t_s -> fastest time)
    #tier_gap = time_gap/(n_tiers - 1)   (Gap between tiers is total time gap divided by n_tiers-1)
    #t_f = (t_0 + t_1) / 2               (Fastest time t_a sits between the first two tier times, t_0 and t_1)
    time_list = [round(t_f - time_gap/(2*(n_tiers-1)),0)]

    #And the time gap between each individual tier
    tier_gap = round(2*(t_f-time_list[0]),0)

    #Create rest of time tiers
    while (time_list[-1] < rank_df[time_column].max()):
        time_list.append(time_list[-1] + tier_gap)

    #Tiers for the list:
    tier_names = tier_list[:len(time_list)-1] #Single string
    tier_names = ' '.join(tier_names) #With spaces
    tier_names = tier_names.split() #List where each item is a tier name

    #Time intervals corresponding to each tier
    time_intervals=[]
    for i in range(0,len(tier_names)):
        #Special cases for first and last cases
        if (i==0):
            time_intervals.append('Less than '+str(time_list[i+1])+' s')
        
        elif (i==len(tier_names)-1):
            time_intervals.append('More than '+str(time_list[i])+' s')
        
        else: #Base case
            time_intervals.append(str(time_list[i])+' s  -  '+str(time_list[i+1])+' s')

    #Weapons in each rank
    tier_weapons=[] #star with empty list

    #Initialize a counter
    counter=1

    #Iterate through all tiers
    for time in tier_names:

        tier = tier_names[0]
            
        #Get the min and maximum allowed times for this tier
        min_time = time_list[counter-1]
        max_time = time_list[counter]

        #Slice the valid portion of rank_df
        slice_df = rank_df[(rank_df[time_column] >= min_time) & (rank_df[time_column] < max_time)]

        #Append list of weapons to tier_weapons
        tier_weapons.append(slice_df[weapon_column].tolist())
        counter += 1

    #Make tier_df to return
    tier_df = pd.DataFrame({'Tier':tier_names,'Average Times':time_intervals,'Weapons':tier_weapons})

    #Set tier column as index
    tier_df = tier_df.set_index('Tier')

    #Convert lists in 'Weapons' column to strings for readability
    tier_df['Weapons'] = tier_df['Weapons'].apply(lambda x: ', '.join(x))

    #Made 'Weapons' column longer for readability and return
    return tier_df.style.set_properties(subset=['Weapons'], **{'width': '400px'})

def remove_outliers(speed_df,weapon_column='Weapon',time_column='Time (s)',quant1=0.25,quant3=0.75,mult=1.5):
    """
    Removes entries with outlier times (defined by time_column), per weapon type
    (defined by weapon_column)
    """

    #First get a list of the different weapons available
    weapon_list = speed_df[weapon_column].unique()

    #Start with an empty dataframe
    no_outliers = pd.DataFrame()

    #Iterate through weapon types
    for weapon in weapon_list:
        #Get a slice with just the current weapon
        temp_df = speed_df[speed_df[weapon_column]==weapon]

        #Define quantiles
        Q1 = temp_df[time_column].quantile(quant1)
        Q3 = temp_df[time_column].quantile(quant3)
        IQR = Q3 - Q1

        #The temp_df with no outliers
        filter_mask = ((temp_df[time_column] >= Q1 - mult * IQR) & (temp_df[time_column] <= Q3 + mult *IQR))
        temp_df = temp_df[filter_mask]

        #Concatenate to output df
        no_outliers=pd.concat([no_outliers,temp_df])

    
    #Return df with no outliers
    return no_outliers