# Synthetic TEST data only (never published): exercises the pipeline end to end.
import csv, random, os
random.seed(1)
cols="EIN,NAME,ICO,STREET,CITY,STATE,ZIP,GROUP,SUBSECTION,AFFILIATION,CLASSIFICATION,RULING,DEDUCTIBILITY,FOUNDATION,ACTIVITY,ORGANIZATION,STATUS,TAX_PERIOD,ASSET_CD,INCOME_CD,FILING_REQ_CD,PF_FILING_REQ_CD,ACCT_PD,ASSET_AMT,INCOME_AMT,REVENUE_AMT,NTEE_CD,SORT_NAME".split(",")
cities={"TX":["HOUSTON","DALLAS","AUSTIN","SAN ANTONIO","WACO"],"LA":["NEW ORLEANS","BATON ROUGE","ALEXANDRIA","SHREVEPORT"]}
out=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"data","raw","TEST"); os.makedirs(out,exist_ok=True)
months=[f"2025{m:02d}" for m in range(9,13)]+[f"2026{m:02d}" for m in range(1,9)]
for st,cs in cities.items():
  with open(f"{out}/eo_{st.lower()}.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols); w.writeheader()
    for i in range(1500 if st=="TX" else 500):
      r={c:"" for c in cols}
      r.update(EIN=f"{random.randint(10**8,10**9-1)}",NAME=f"TEST ORG {i} OF {st} FOUNDATION INC",CITY=random.choice(cs),STATE=st,
        ZIP="70000",SUBSECTION=random.choice(["03"]*9+["04"]),RULING=random.choice(months+["199805","201203"]*3),
        DEDUCTIBILITY="1",FOUNDATION=random.choice(["15","16","10"]),FILING_REQ_CD=random.choice(["01","02"]),
        NTEE_CD=random.choice(["B20","P30","X20","N60","A20",""]),STREET="1 MAIN ST")
      w.writerow(r)
