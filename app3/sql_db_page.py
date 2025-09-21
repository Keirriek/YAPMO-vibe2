from nicegui import ui
import globals, config
import json
import sqlite3

class SqlDBUI:
    def __init__(self):
        self.max_result_display_lines = int(globals.config_data.get('max_result_display_lines', 1000))
        self.total_rows = 0
        self.current_query = None
        self.queries = []
        self.custom_query = None
        self.load_queries()
        
    def load_queries(self):
        """Load queries from JSON file specified in config"""
        try:
            json_file = globals.config_data.get('sqlfile', 'yapmo.json')
            with open(json_file, 'r') as f:
                data = json.load(f)
                self.queries = data.get('queries', [])
        except Exception as e:
            ui.notify(f'Error loading queries: {str(e)}', type='negative')
            self.queries = []

    def validate_row_numbers(self, start_row, end_row):
        """Validate start and end row numbers"""
        # Skip validation als limit=False
        if self.current_query and not self.current_query.get('limit', True):
            return True

        if start_row < 1:
            ui.notify('Start row must be >= 1', type='warning')
            return False
        if end_row < start_row:
            ui.notify('End row must be >= Start row', type='warning')
            return False
        if end_row - start_row + 1 > self.max_result_display_lines:
            ui.notify(f'Maximum {self.max_result_display_lines} rows can be displayed', type='warning')
            return False
        if start_row > self.total_rows or end_row > self.total_rows:
            ui.notify(f'Row numbers must be <= {self.total_rows}', type='warning')
            return False
        return True

    def execute_query(self, query, start_row, end_row):
        """Execute SQL query and return results"""
        try:
            conn = sqlite3.connect(globals.config_data['db'])
            cursor = conn.cursor()
            
            # Check if it's a SELECT query
            is_select = query.strip().upper().startswith('SELECT')
            
            if is_select:
                # For SELECT queries, get results
                cursor.execute(query)
                all_rows = cursor.fetchall()
                self.total_rows = len(all_rows)
                
                # Validate row numbers
                if not self.validate_row_numbers(start_row, end_row):
                    return None, None
                
                # Get column names
                columns = [description[0] for description in cursor.description]
                
                # Get requested rows
                rows = all_rows[start_row-1:end_row]
                
                conn.close()
                return columns, rows
                
            else:
                # For non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
                cursor.execute(query)
                conn.commit()
                affected_rows = cursor.rowcount
                conn.close()
                
                # Return special format for non-SELECT queries
                columns = ['Result']
                rows = [[f"Query executed successfully. Rows affected: {affected_rows}"]]
                return columns, rows
                
        except Exception as e:
            ui.notify(f'Error executing query: {str(e)}', type='negative')
            if conn:
                conn.close()
            return None, None

def content():
    css_border = 'border-2 border-blue-500 rounded-lg'
    sql_ui = SqlDBUI()
    
    def get_column_widths(columns, rows):
        """Calculate maximum width for each column based on content"""
        widths = {col: len(str(col)) for col in columns}  # Start with header lengths
        
        # Check all values in each column
        for row in rows:
            for col_idx, value in enumerate(row):
                col_name = columns[col_idx]
                widths[col_name] = max(widths[col_name], len(str(value)))
        
        # Convert character counts to pixels (approximate)
        return {col: f"min-w-[{max(width * 8 + 32, 150)}px]" for col, width in widths.items()}

    def update_query_info(selected_name):
        """Update UI with selected query information"""
        if selected_name:
            selected_query = next((q for q in sql_ui.queries if q['name'] == selected_name), None)
            if selected_query:
                sql_ui.current_query = selected_query
                query_name_label.text = f"{selected_query['name']} - {selected_query['description']}"
                query_code_area.value = selected_query['query']

    def execute_current_query():
        """Execute currently selected or custom query"""
        query_to_execute = query_code_area.value
        if not query_to_execute:
            ui.notify('Please enter a query or select a predefined one', type='warning')
            return
            
        columns, rows = sql_ui.execute_query(
            query_to_execute,
            int(start_row.value),
            int(end_row.value)
        )
        
        if columns and rows:
            # Calculate column widths
            col_widths = get_column_widths(columns, rows)
            
            with results_area:
                results_area.clear()
                # Headers
                with ui.row().classes('font-bold border-b-2 p-2 min-w-max'):
                    for col in columns:
                        ui.label(col).classes(f'px-4 {col_widths[col]}').style('white-space: nowrap')
                
                # Data rows
                for row in rows:
                    with ui.row().classes('border-b p-2 min-w-max'):
                        for col_idx, value in enumerate(row):
                            col_name = columns[col_idx]
                            ui.label(str(value)).classes(f'px-4 {col_widths[col_name]}').style('white-space: nowrap')

    def clear_form():
        """Reset the form"""
        sql_ui.current_query = None
        query_select.value = None  # Reset dropdown
        query_name_label.text = ''
        start_row.value = 1
        end_row.value = 5
        query_code_area.value = ''
        with results_area:
            results_area.clear()
            ui.label('Results')

    # UI Layout
    ui.label('SQL Database Query').classes('text-h4 mb-4')
    
    # Eerste rij met controls
    with ui.row().classes('w-full items-center'):
        # Query selection dropdown
        query_select = ui.select(
            label='SQL query',
            options=[q['name'] for q in sql_ui.queries],
            on_change=lambda e: update_query_info(e.value)
        ).classes('w-1/4')
        
        # Query naam label
        query_name_label = ui.label('').classes('w-2/5 pl-2 pt-4 pb-4 ' + css_border)
        
        # Start en end row inputs - altijd zichtbaar maken
        start_row = ui.number('Start row:', value=1, min=1, format='%i').classes('pl-2 ' + css_border)
        end_row = ui.number('End row:', value=5, min=1, format='%i').classes('pl-2 ' + css_border)
        
        # Execute button
        ui.button('Execute', on_click=execute_current_query).classes('bg-blue-500')
    
    # Query code area - now using a textarea
    query_code_area = ui.textarea('SQL Query (Editable)', placeholder='Enter your SQL query here...').classes('w-full ' + css_border).style('min-height: 100px; font-family: monospace;')
    
    # Results area
    with ui.scroll_area().classes('w-full h-80 ' + css_border).style('overflow: auto'):
        results_area = ui.column().classes('w-full')
        with results_area:
            ui.label('Results')
    
    # Bottom buttons
    with ui.row().classes('w-full items-center'):
        ui.button('Clear', on_click=clear_form)
        ui.button('Menu', on_click=lambda: ui.navigate.to('/'))

if __name__ in {"__main__", "__mp_main__"}:
    config.init_config()
    ui.run(title='SQL Database Query')