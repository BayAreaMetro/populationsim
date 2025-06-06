USAGE = r"""

  Summarizes the synthesized households and persons file back to
  tazdata to check things validate ok.

  Writes popsyn_taz_summary.csv to the cwd with columns:
  * TAZ
  * pemploy_[1234] = number of persons with this pemploy value
  * pstudent_[123] = numver of persons with this pstudent value
  * UNITTYPE_[13] = number of persons with UNITTYPE value

  References: 
  * https://github.com/BayAreaMetro/modeling-website/wiki/PopSynHousehold
  * https://github.com/BayAreaMetro/modeling-website/wiki/PopSynPerson

"""

import argparse, pathlib, sys
import numpy, pandas

if __name__ == "__main__":
    pandas.options.display.width    = 180
    pandas.options.display.max_rows = 1000

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=USAGE)
    parser.add_argument("household_file", help="Household file")
    parser.add_argument("person_file",    help="Person file")
    args = parser.parse_args()

    print(args)

    household_file = pathlib.Path(args.household_file)
    person_file = pathlib.Path(args.person_file)

    # This will likely expand but for now, focus on summarizing pemploy
    household_df = pandas.read_csv(household_file)
    print(f"Read {len(household_df):,} lines from {household_file}")
    print(household_df.head())

    person_df = pandas.read_csv(person_file)
    print(f"Read {len(person_df):,} lines from {person_file}")
    # join with persons
    person_df = pandas.merge(
        left=person_df,
        right=household_df,
        on="HHID",
        how="left",
        validate="many_to_one"
    )
    print(f"person_df len={len(person_df):,}, head=\n{person_df.head()}")

    # summarize pemploy categories by TAZ
    person_taz_pemploy = person_df.groupby(["TAZ","pemploy"]).size().reset_index(drop=False, name="persons")
    person_taz_pemploy = person_taz_pemploy.pivot_table(index="TAZ", columns="pemploy", values="persons", fill_value=0).reset_index(drop=False)
    # print(person_taz_pemploy.head())
    # print(f"index.name={person_taz_pemploy.index.name}  columns={person_taz_pemploy.columns}")

    pemploy_cols_rename = {}
    for col in person_taz_pemploy.columns.tolist():
      if col == "TAZ": continue
      pemploy_cols_rename[ col ] = f"pemploy_{col}"
    
    person_taz_pemploy.rename(columns=pemploy_cols_rename, inplace=True)
    person_taz_pemploy.columns.name = None
    person_taz_pemploy[list(pemploy_cols_rename.values())] = person_taz_pemploy[list(pemploy_cols_rename.values())].astype(int)
    print(person_taz_pemploy.head())

    # summarize pstudent categories by TAZ
    person_taz_pstudent = person_df.groupby(["TAZ","pstudent"]).size().reset_index(drop=False, name="persons")
    person_taz_pstudent = person_taz_pstudent.pivot_table(index="TAZ", columns="pstudent", values="persons", fill_value=0).reset_index(drop=False)
    # print(person_taz_pstudent.head())
    # print(f"index.name={person_taz_pstudent.index.name}  columns={person_taz_pstudent.columns}")

    pstudent_cols_rename = {}
    for col in person_taz_pstudent.columns.tolist():
      if col == "TAZ": continue
      pstudent_cols_rename[ col ] = f"pstudent_{col}"
    
    person_taz_pstudent.rename(columns=pstudent_cols_rename, inplace=True)
    person_taz_pstudent.columns.name = None
    person_taz_pstudent[list(pstudent_cols_rename.values())] = person_taz_pstudent[list(pstudent_cols_rename.values())].astype(int)
    print(person_taz_pstudent.head())

    taz_summary = pandas.merge(
      left=person_taz_pemploy,
      right=person_taz_pstudent,
      on="TAZ",
      how="outer",
      validate="one_to_one")
    
    # summarize UNITTYPE categories by TAZ
    person_taz_gqphh = person_df.groupby(["TAZ","UNITTYPE"]).agg(
       persons   =pandas.NamedAgg(column="PERID", aggfunc="nunique"),
       households=pandas.NamedAgg(column="HHID",  aggfunc="nunique")
    ).reset_index(drop=False)
    person_taz_gqphh = person_taz_gqphh.pivot_table(index="TAZ", columns="UNITTYPE", values=["persons","households"], fill_value=0).reset_index(drop=False)
    print(f"index.name={person_taz_gqphh.index.name}  columns=\n{person_taz_gqphh.columns}")
    print(person_taz_gqphh.head())

    unittype_cols_rename = []
    for col in person_taz_gqphh.columns.tolist():
      print(f"{col=}")
      if col[0] == "TAZ": 
        unittype_cols_rename.append("TAZ")
      else:
        unittype_cols_rename.append(f"{col[0]}_UnitType{col[1]}")
    print(f"{unittype_cols_rename=}")

    person_taz_gqphh.columns = unittype_cols_rename
    person_taz_gqphh.columns.name = None
    person_taz_gqphh[unittype_cols_rename] = person_taz_gqphh[unittype_cols_rename].astype(int)
    print(person_taz_gqphh.head())

    # join to taz_summary
    taz_summary = pandas.merge(
      left=taz_summary,
      right=person_taz_gqphh,
      on="TAZ",
      how="outer",
      validate="one_to_one")
    
    taz_summary.to_csv("popsyn_taz_summary.csv", index=False)
    print(f"Wrote {len(taz_summary):,} lines to popsyn_taz_summary.csv")
