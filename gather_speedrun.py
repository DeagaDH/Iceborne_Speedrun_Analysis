import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

class IBSpeedrunTableParser:
       
        def parse_url(self, url):
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            
            #Find table
            table=soup.find('table')
            
            #Return as a dataframe
            return self.parse_html_table(table)
    
        def parse_html_table(self,table):
            n_columns = 0
            n_rows=0
            column_names = []
            
            # Find number of rows and columns
            # we also find the column titles if we can
            for row in table.find_all('tr'):
                
                # Determine the number of rows in the table
                td_tags = row.find_all('td')
                if len(td_tags) > 0:
                    n_rows+=1
                    if n_columns == 0:
                        # Set the number of columns for our table
                        n_columns = len(td_tags)
                        
                # Handle column names if we find them
                th_tags = row.find_all('th') 
                if len(th_tags) > 0 and len(column_names) == 0:
                    for th in th_tags:
                        column_names.append(th.get_text())
    
            # Safeguard on Column Titles
            if len(column_names) > 0 and len(column_names) != n_columns:
                raise Exception("Column titles do not match the number of columns")
    
            columns = column_names if len(column_names) > 0 else range(0,n_columns)
            df = pd.DataFrame(columns = columns,
                              index= range(0,n_rows))
            row_marker = 0
            for row in table.find_all('tr'):
                column_marker = 0
                columns = row.find_all('td')
                for column in columns:
                    if (column.get_text() != ''):
                        df.iat[row_marker,column_marker] = column.get_text().replace('\n','')
                    else:
                        df.iat[row_marker,column_marker] = self.get_weapon_type(column)
                    column_marker += 1
                if len(columns) > 0:
                    row_marker += 1
            
            return df

        def get_weapon_type(self,column):
            """
            Gets the weapon type from img src for the weapon column
            """
            
            #Weapon name as a link in the form '/static/weapon-icon/weapon-name.png'
            weapon_name = column.find('img')['src']
            
            #Weapon name as 'weapon-name.png'
            weapon_name= weapon_name.split('/')[3]
            
            #Weapon name as 'weapon-name'
            weapon_name = weapon_name.split('.')[0]
            
            #Weapon name as 'Weapon Name'
            weapon_name = weapon_name.replace('-',' ').title()
            
            return weapon_name

#Getting links to all monster pages from the main page

main_url = 'https://mhwleaderboards.com/'

main_page = requests.get(main_url)

soup = BeautifulSoup(main_page.content, "html.parser")

#Get categories (6*, 5*, etc)
monster_categories = soup.find_all('div',{'class': lambda L: L and L.endswith('star')})

#Get amount of monsters to initialize dataframe
monster_count = len(soup.find_all('li',{'class':''}))

link_df = pd.DataFrame(columns=['Monster Name','Star Rating','Link'],index=range(0,monster_count))

count=0
for category in monster_categories:
    
    #List of monsters in the current star category
    monster_list = category.find_all('li',{'class':''})
    
    #Cycle through all monsters in the category
    for monster in monster_list:
        #Full monster name
        full_name = monster.get_text()

        #Check for Safi'Jiiva (Full Energy)
        if ('Full Energy' in full_name):
            link_df.at[count,'Monster Name'] = "Safi'jiiva (Full Energy)" #Only exception
        else: #All other monster names
            link_df.at[count,'Monster Name'] = monster.get_text().split('(')[0] #Monster name + space before parenthesis
            link_df.at[count,'Monster Name'] = link_df.at[count,'Monster Name'][:-1] #Remove space
        
        #Star Rating
        link_df.at[count,'Star Rating'] = category.find('h5').get_text()[0] #First character is the star rating
        
        #Link
        link_df.at[count,'Link'] = main_url[:-1]+monster.find('a')['href'] #Main URL + link for each monster
        count += 1

#Create one Dataframe to store all speedrun data
speed_df = pd.DataFrame(columns=['Star Rating','Monster Name','Quest','Runner','Time','Weapon','Platform','Ruleset'])

#Instantiate table parser object
table_parser = IBSpeedrunTableParser()

#Get Dataframes for each monster and append those to speed_df
for index in link_df.index:

    #Print statemant for how it's going
    print(f"Gathering speedrun data for {link_df['Monster Name'][index]}...")
    url = link_df['Link'][index]

    #Get Dataframe for the monster
    mon_df = table_parser.parse_url(url)

    #Add columns for monster name and star rating
    mon_df.insert(0, 'Monster Name', link_df['Monster Name'][index])
    mon_df.insert(0, 'Star Rating', link_df['Star Rating'][index])

    #Append to speed_df
    speed_df = speed_df.append(mon_df)

    #Wait to not overload server
    time.sleep(30)

#Save to a csv file
speed_df.to_csv('speedrun_data.csv',index=False)