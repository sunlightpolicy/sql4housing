
From 2001 to 2015, the share of households considered “rent burdened”- spending over 30 percent of income on rent-has increased by 19 percent. For these households, housing, an essential human need, has become a persistent source of financial and social stress. 

Many cities have struggled to keep housing supply in pace with increased demand, and tenants’ rights have become a focal point for local advocates and, increasingly, policy-makers. Despite public efforts to protect tenants, city governments don’t hold landlords accountable to maintaining their properties, and let developers lobby against tenant protection laws in order to buy and flip properties with short turnaround.

# Civic Hacking in Housing Advocacy

Housing advocates have an essential role to play in protecting residents from the consequences of real estate speculation. But they’re often at a significant disadvantage; the real estate lobby has access to a wealth of data and technological expertise. Civic hackers and open data could play an essential role in leveling the playing field.

Civic hackers have facilitated wins for housing advocates by scraping data or submitting FOIA requests where data is not open and creating apps to help advocates gain insights that they can turn into action. 

Hackers at New York City’s Housing Data Coalition created a host of civic apps that identify problematic landlords by exposing owners behind shell companies, or flagging buildings where tenants are at risk of displacement. In a similar vein, Washington DC’s Housing Insights tool aggregates a wide variety of data to help advocates make decisions about affordable housing.

# Barriers and opportunities

Today, the degree to which housing data exists, is openly available, and consistently reliable varies widely, even within cities themselves. Cities with robust communities of affordable housing advocacy groups may not be connected to people who can help open data and build usable tools. Even in cities with robust advocacy and civic tech communities, these groups may not know how to work together because of the significant institutional knowledge that’s required to understand how to best support housing advocacy efforts.

In cities where civic hackers have tried to create useful open housing data repositories, similar data cleaning processes have been replicated, such as record linkage of building owners or identification of rent-controlled units. Civic hackers need to take on these data cleaning and “extract, transform, load” (ETL) processes in order to work with the data itself, even if it’s openly available. The Housing Data Coalition has assembled NYC-DB, a tool which builds a postgres database containing a variety of housing related data pertaining to New York City, and Washington DC’s Housing Insights similarly ingests housing data into a postgres database and API for front-end access. 

Since these tools are open source, civic hackers in a multitude of cities can use existing work to develop their own, locally relevant tools to support local housing advocates. 

# Soliciting feedback on a new project for usable housing data

Throughout this summer, I’m going to build a tool for civic hackers to create databases of housing data for their own cities. My goal is to build on the work that civic hackers have initiated in New York, DC, and elsewhere, thereby reducing the startup effort required to develop apps to support housing advocacy efforts.

If you’re a civic hacker, advocate, policy expert, or anyone else working to make housing advocacy easier, I need your help! Are there significant barriers you’re facing where you could benefit from the expertise of other cities? Do you have open source tools which could be adapted for other cities to use? Has your city opened up a value source of data that you don’t know how to work with? If you’re interested in reviewing or advising on this project, please email kchan@sunlightfoundation.com or comment below. You can also follow along with this project on our GitHub.

