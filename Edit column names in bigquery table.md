# Introduction
This is a step-by-step guide to help you change the name of a column in bigquery tables.

From official [google docs](https://cloud.google.com/bigquery/docs/manually-changing-schemas) we cannot just rename the column name in the table.  
Google offers two solutions to this problem.
The first solution looks imperfect, because after applying this method. All field modifiers become **NULLABLE**.
The second also looks imperfect. We'll have to export the files to a new bucket. Using files no larger than 1 GB. After that, create a new table with a new schema, and import it back.  

## Step 1: Creating table with new schema in bigquery
---
In the **explorer** in bigquery in the dataset. Click on the ```⋮```to the right of the dataset name. And select the item **Create table**.  
![create table](https://user-images.githubusercontent.com/38936255/146343440-b3db5c50-19b9-4314-9c7e-f82ca012d870.png)  
Create a new table using the schema with the changed name of the field or fields.  
At the end of the first step, you should have two tables. One original, the second with a modified schema.  
![img](https://user-images.githubusercontent.com/38936255/146344509-2aecf8bb-119c-455b-ba44-a95924bcc532.png)  
## Step 2: Import data from original table to new table created with the new schema.
---
Importing data into a new table will be done using a query:  
```
SELECT
 * EXCEPT(column_one, column_two),
 column_one AS newcolumn_one, column_two AS newcolumn_two
FROM
 mydataset.my_new_schema_table
```
After creating query with your initial data. It is necessary to specify in the query settings to which table the data will be transferred. To do this, need to go to the **Query Settings**.  

![img](https://user-images.githubusercontent.com/38936255/146346033-33474622-b910-4315-8eb0-cd7f2e95dd50.png)

Perform following steps under **Destination** tab:  
1. Select **Set a destination table for query results**.  
2. Select **Dataset name**.  
3. Enter the name of the table to which export the data.  
4. Select in **Destination table write preference** action **Append to table**.  
5. Click **Save**.

![img](https://user-images.githubusercontent.com/38936255/146348178-978cb3ae-64dd-43a1-b236-c6f9e7007de2.png)  

After that, run the query and wait for it to complete successfully.

## Step 3: Replacing an old table with a new
---
*Recommended: Before proceeding, make a backup copy of the current table to protect yourself.*

In this step, we are deleting the old table. And replacing it with a new one with a new field or fields name.

1. Click on the ```⋮``` to the right of the old table name. And select **Delete**.
2. Click on the ```⋮``` to the right of the table with new schema. And select **Open**
3. Then at the top in the settings select **COPY**  
![img](https://user-images.githubusercontent.com/38936255/146350078-faa04f01-18c6-4975-8de9-05ccf836e551.png)  
4. Enter the name of the old remote table.
5. Click to **Copy**.
6. If all went well, delete the table from which the new one was copied.


*After all the actions, the dataset should contain table with the original name but already with a changed name or column names.*



