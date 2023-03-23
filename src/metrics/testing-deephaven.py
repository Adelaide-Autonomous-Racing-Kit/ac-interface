from pydeephaven import Session
session = Session() # assuming Deephaven Community Edition is running locally with the default configuration
table1 = session.time_table(period=1000000000).update(formulas=["Col1 = i % 2"])
df = table1.to_arrow().to_pandas()
print(df)
session.close()
