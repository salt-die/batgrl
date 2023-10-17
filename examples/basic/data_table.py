"""
An example usage of data tables.
"""
from batgrl.app import App
from batgrl.gadgets.data_table import ColumnStyle, DataTable

TABLE = {
    "Name": [
        "George Lucas",
        "Steven Spielberg",
        "James Cameron",
        "Peter Jackson",
        "Ridley Scott",
    ],
    "Net Worth (Millions)": [7_620, 5_410, 700, 450, 400],
    "Age": [75, 74, 66, 58, 82],
    "Country": [
        "United States",
        "United States",
        "Canada",
        "New Zealand",
        "United Kingdom",
    ],
}


class TableApp(App):
    async def on_start(self):
        table_1 = DataTable(data=TABLE, select_items="row", size=(7, 60))
        table_2 = DataTable(
            select_items="column",
            zebra_stripes=False,
            allow_sorting=False,
            default_style=ColumnStyle(alignment="center", padding=3),
            size=(7, 60),
        )
        table_2.top = table_1.bottom + 1
        for column_label in TABLE:
            table_2.add_column(column_label)
        for i in range(len(TABLE["Name"])):
            table_2.add_row([column[i] for column in TABLE.values()])

        self.add_gadgets(table_1, table_2)


if __name__ == "__main__":
    TableApp(title="Data Table Example").run()
