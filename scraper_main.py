import os,time
# from dotenv import load_dotenv
from service import RepVueService
from functions.exceptions import CompanyNotFound

# load_dotenv()

#credentials
email_id = "coderk210@gmail.com"          # KeyError if missing
password = "Black2001@1315" 

#company name   
Company_name = "Salesforce"

try:

    with RepVueService.create() as svc:
        svc.driver.get("https://www.repvue.com/login")
        svc.login(email_id, password)

        try:
            url = svc.search(Company_name)
            print("Navigated to:", url)
        except CompanyNotFound as e:
            print(e)


        

        time.sleep(4)

        info = svc.general_info()
        perf = svc.performance()

        slug = svc.company_slug()
        if slug:
            svc.go("salaries",slug)
            salaries = svc.salaries()

        print(info)
        print(perf)
        print(salaries)
        svc.driver.close()
finally:
    print('Scraping done')
