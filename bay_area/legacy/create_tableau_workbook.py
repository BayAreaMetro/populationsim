"""
Create a Tableau workbook with pre-configured parameter for measure selection.
This automates the manual setup of parameters and calculated fields.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path

# Define measures to include in the parameter
MEASURES = [
    ("HH", "Households"),
    ("POP", "Population"),
    ("emp_total", "Total Employment"),
    ("ret_loc", "Local Retail"),
    ("ret_reg", "Regional Retail"),
    ("health", "Healthcare"),
    ("ed_k12", "K-12 Education"),
    ("ed_high", "Higher Education"),
    ("ed_oth", "Other Education"),
    ("eat", "Food Service"),
    ("hotel", "Hotel/Lodging"),
    ("serv_bus", "Business Services"),
    ("serv_pers", "Personal Services"),
    ("serv_soc", "Social Services"),
    ("prof", "Professional Services"),
    ("fire", "Finance/Insurance/Real Estate"),
    ("info", "Information"),
    ("gov", "Government"),
    ("man_tech", "Tech Manufacturing"),
    ("man_bio", "Bio Manufacturing"),
    ("man_lgt", "Light Manufacturing"),
    ("man_hvy", "Heavy Manufacturing"),
    ("transp", "Transportation"),
    ("logis", "Logistics/Warehousing"),
    ("constr", "Construction"),
    ("util", "Utilities"),
    ("natres", "Natural Resources"),
    ("ag", "Agriculture"),
    ("art_rec", "Arts/Recreation"),
    ("lease", "Leasing")
]

def create_tableau_workbook():
    """Create a Tableau TWB file with pre-configured parameter and calculated field."""
    
    # Paths
    tableau_dir = Path("output_2023/tableau")
    maz_shapefile = tableau_dir / "maz_boundaries_tableau.shp"
    maz_data = tableau_dir / "maz_data_tableau.csv"
    output_file = tableau_dir / "MAZ_Dashboard.twb"
    
    # Create parameter XML - List of measure names for dropdown
    parameter_members = []
    for field_name, display_name in MEASURES:
        parameter_members.append(f'          <member alias="{display_name}" value="{field_name}" />')
    
    parameter_members_xml = '\n'.join(parameter_members)
    
    # Create calculated field CASE statement
    case_conditions = []
    for field_name, display_name in MEASURES:
        case_conditions.append(f'  WHEN [Parameters].[Select Measure] = "{field_name}" THEN [maz_data_tableau.csv].[{field_name}]')
    
    case_statement = '\n'.join(case_conditions)
    
    # Tableau workbook XML template
    twb_content = f'''<?xml version='1.0' encoding='utf-8' ?>

<workbook source-build='2024.1.0 (20241.24.0220.1108)' source-platform='win' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest>
    <_.fcp.AnimationOnByDefault.true...AnimationOnByDefault />
    <_.fcp.MarkAnimation.true...MarkAnimation />
    <_.fcp.ObjectModelEncapsulateLegacy.true...ObjectModelEncapsulateLegacy />
    <_.fcp.ObjectModelTableType.true...ObjectModelTableType />
    <_.fcp.SchemaViewerObjectModel.true...SchemaViewerObjectModel />
    <SheetIdentifierTracking />
    <WindowsPersistSimpleIdentifiers />
  </document-format-change-manifest>
  <preferences>
    <preference name='ui.encoding.shelf.height' value='24' />
    <preference name='ui.shelf.height' value='26' />
  </preferences>
  <datasources>
    <datasource caption='maz_boundaries_tableau+ (maz_boundaries_tableau)' inline='true' name='federated.1234567' version='18.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='maz_boundaries_tableau' name='shapefile.12345678'>
            <connection class='shapefile' dbname='{maz_shapefile.absolute()}' filename='{maz_shapefile.absolute()}' server='' />
          </named-connection>
          <named-connection caption='maz_data_tableau' name='textscan.12345679'>
            <connection class='textscan' directory='{tableau_dir.absolute()}' filename='maz_data_tableau.csv' server='' />
          </named-connection>
        </named-connections>
        <relation connection='shapefile.12345678' name='maz_boundaries_tableau' table='[maz_boundaries_tableau]' type='table'>
          <columns>
            <column datatype='integer' name='MAZ_ID' ordinal='0' />
            <column datatype='geometry' name='Geometry' ordinal='1' />
          </columns>
        </relation>
        <relation join='left' type='join'>
          <clause type='join'>
            <expression op='='>
              <expression op='[maz_boundaries_tableau].[MAZ_ID]' />
              <expression op='[maz_data_tableau.csv].[MAZ_ID]' />
            </expression>
          </clause>
          <relation connection='shapefile.12345678' name='maz_boundaries_tableau' table='[maz_boundaries_tableau]' type='table' />
          <relation connection='textscan.12345679' name='maz_data_tableau.csv' table='[maz_data_tableau#csv]' type='table' />
        </relation>
        <cols>
          <map key='[MAZ_ID]' value='[maz_boundaries_tableau].[MAZ_ID]' />
          <map key='[Geometry]' value='[maz_boundaries_tableau].[Geometry]' />
        </cols>
      </connection>
      <aliases enabled='yes' />
      <column caption='MAZ ID' datatype='integer' name='[MAZ_ID]' role='dimension' type='ordinal' />
      <column caption='Geometry' datatype='geometry' name='[Geometry]' role='measure' type='quantitative' />
      <_.fcp.ObjectModelEncapsulateLegacy.true...object-graph>
        <objects>
          <object caption='maz_boundaries_tableau+ (maz_boundaries_tableau)' id='federated.1234567'>
            <properties context=''>
              <relation join='left' type='join'>
                <clause type='join'>
                  <expression op='='>
                    <expression op='[maz_boundaries_tableau].[MAZ_ID]' />
                    <expression op='[maz_data_tableau.csv].[MAZ_ID]' />
                  </expression>
                </clause>
                <relation connection='shapefile.12345678' name='maz_boundaries_tableau' table='[maz_boundaries_tableau]' type='table' />
                <relation connection='textscan.12345679' name='maz_data_tableau.csv' table='[maz_data_tableau#csv]' type='table' />
              </relation>
            </properties>
          </object>
        </objects>
      </_.fcp.ObjectModelEncapsulateLegacy.true...object-graph>
      <layout _.fcp.SchemaViewerObjectModel.false...dim-percentage='0.5' _.fcp.SchemaViewerObjectModel.false...measure-percentage='0.4' dim-ordering='alphabetic' measure-ordering='alphabetic' show-structure='true' />
      <semantic-values>
        <semantic-value key='[Country].[Name]' value='&quot;United States&quot;' />
      </semantic-values>
      <_.fcp.ObjectModelTableType.true...column caption='maz_boundaries_tableau' datatype='table' name='[__tableau_internal_object_id__].[maz_boundaries_tableau_12345678]' role='measure' type='quantitative' />
      <_.fcp.ObjectModelTableType.true...column caption='maz_data_tableau.csv' datatype='table' name='[__tableau_internal_object_id__].[maz_data_tableau.csv_12345679]' role='measure' type='quantitative' />
      <column-instance column='[MAZ_ID]' derivation='None' name='[none:MAZ_ID:nk]' pivot='key' type='nominal' />
      <column-instance column='[Geometry]' derivation='None' name='[none:Geometry:nk]' pivot='key' type='nominal' />
    </datasource>
  </datasources>
  <worksheets>
    <worksheet name='MAZ Map'>
      <table>
        <view>
          <datasources>
            <datasource caption='maz_boundaries_tableau+ (maz_boundaries_tableau)' name='federated.1234567' />
          </datasources>
          <datasource-dependencies datasource='federated.1234567'>
            <column caption='Selected Measure' datatype='real' name='[Calculation_1234567890]' role='measure' type='quantitative'>
              <calculation class='tableau' formula='CASE [Parameters].[Select Measure]
{case_statement}
END' />
            </column>
            <column caption='Geometry' datatype='geometry' name='[Geometry]' role='measure' type='quantitative' />
            <column-instance column='[Geometry]' derivation='None' name='[none:Geometry:nk]' pivot='key' type='nominal' />
            <column-instance column='[Calculation_1234567890]' derivation='Sum' name='[sum:Calculation_1234567890:qk]' pivot='key' type='quantitative' />
          </datasource-dependencies>
          <aggregation value='true' />
        </view>
        <style />
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Automatic' />
            <encodings>
              <color column='[federated.1234567].[sum:Calculation_1234567890:qk]' />
              <geometry column='[federated.1234567].[none:Geometry:nk]' />
            </encodings>
          </pane>
        </panes>
        <rows />
        <cols />
      </table>
      <simple-id uuid='{{12345678-1234-1234-1234-123456789012}}' />
    </worksheet>
  </worksheets>
  <windows source-height='30'>
    <window class='worksheet' name='MAZ Map'>
      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
            <card pane-specification-id='0' param='[federated.1234567].[sum:Calculation_1234567890:qk]' type='color' />
          </strip>
        </edge>
        <edge name='top'>
          <strip size='2147483647'>
            <card type='columns' />
          </strip>
          <strip size='2147483647'>
            <card type='rows' />
          </strip>
          <strip size='31'>
            <card type='title' />
          </strip>
        </edge>
      </cards>
      <viewpoint>
        <highlight>
          <color-one-way>
            <field>[federated.1234567].[none:Geometry:nk]</field>
          </color-one-way>
        </highlight>
      </viewpoint>
      <simple-id uuid='{{23456789-2345-2345-2345-234567890123}}' />
    </window>
  </windows>
  <parameters>
    <parameter name='[Parameters].[Select Measure]' caption='Select Measure' datatype='string' value='HH'>
      <aliases>
{parameter_members_xml}
      </aliases>
    </parameter>
  </parameters>
</workbook>
'''
    
    # Write the workbook file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(twb_content)
    
    print(f"Created Tableau workbook: {output_file}")
    print(f"\nConfigured with {len(MEASURES)} measures:")
    for field_name, display_name in MEASURES[:5]:
        print(f"  - {display_name} ({field_name})")
    print(f"  ... and {len(MEASURES) - 5} more")
    print("\nTo use:")
    print("1. Open MAZ_Dashboard.twb in Tableau Desktop")
    print("2. The 'Select Measure' parameter dropdown will be visible")
    print("3. The map will automatically update when you change the selection")
    
    return output_file

if __name__ == "__main__":
    create_tableau_workbook()
