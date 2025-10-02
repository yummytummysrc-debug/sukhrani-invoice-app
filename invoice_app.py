import datetime
import json
import os
import sys
import tempfile
from pathlib import Path 
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors

def writable_data_path(filename):
    """
    For web deployment, we'll use temp directory instead of local files
    since most cloud platforms have read-only file systems
    """
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        # For web deployment, use temp directory
        base_path = tempfile.gettempdir()
    return os.path.join(base_path, filename)

# File paths (these won't be used in web version, but kept for compatibility)
SKU_FILE = writable_data_path('sku_data.json')
CUSTOMER_FILE = writable_data_path('customer_data.json')
VEHICLE_FILE = writable_data_path('vehicle_data.json')

DEFAULT_SKU_DATA = {
    "Tomato Sauce": {"hsn": "2103", "cgst": 0.025, "sgst": 0.025, "weights": ["4.5 Kg", "650 mL", "5 L"]},
    "Chilly Sauce": {"hsn": "2103", "cgst": 0.025, "sgst": 0.025, "weights": ["4.5 Kg", "650 mL", "5 L"]},
    "Soya Sauce": {"hsn": "2103", "cgst": 0.025, "sgst": 0.025, "weights": ["4.5 Kg", "650 mL", "5 L"]},
    "Vinegar": {"hsn": "2209", "cgst": 0.09, "sgst": 0.09, "weights": ["650 mL", "4.5 Kg", "5 L"]},
    "Ganna Vinegar": {"hsn": "2209", "cgst": 0.09, "sgst": 0.09, "weights": ["650 mL", "4.5 Kg", "5 L"]},
    "Jamun Vinegar": {"hsn": "2209", "cgst": 0.09, "sgst": 0.09, "weights": ["650 mL", "4.5 Kg", "5 L"]},
    "Noodles": {"hsn": "1902", "cgst": 0.09, "sgst": 0.09, "weights": ["500 gm", "1 Kg"]},
    "PET Bottle": {"hsn": "3923", "cgst": 0.09, "sgst": 0.09, "weights": []},
    "PET Preform": {"hsn": "3923", "cgst": 0.09, "sgst": 0.09, "weights": []}
}
DEFAULT_CUSTOMER_DATA = {"Rudauli": [{"name": "Prakash & Sons", "id_type": "GSTN", "id_value": "09AUHPP5426C1ZM"}]}
DEFAULT_VEHICLE_DATA = {"vehicles": []}

# For web deployment, we'll use temp directory for invoice generation
INVOICE_SAVE_PATH = Path(tempfile.gettempdir()) / "invoices"

def load_data(file_path, default_data):
    """
    Modified for web - since we can't persist files, we'll always return default data
    In the web version, data persistence is handled by Streamlit session state
    """
    return default_data

def save_data(file_path, data):
    """
    Modified for web - in web version, data is saved to session state instead of files
    This function is kept for compatibility but doesn't actually save to files
    """
    print(f"Data would be saved to {file_path} (web version uses session state)")

def recalculate_totals(items_list):
    total_amount = sum(item['amount'] for item in items_list)
    total_tax = sum(item['tax'] for item in items_list)
    return {"amount": total_amount, "tax": total_tax, "grand_total": total_amount + total_tax}

def apply_price_adjustments(invoice_items):
    # This logic may need updating based on new item names
    return invoice_items, recalculate_totals(invoice_items), []

def format_tax_percentage(decimal_rate):
    """Format tax rate as percentage"""
    percentage = decimal_rate * 100
    if percentage == int(percentage):
        return f"{int(percentage)}%"
    else:
        return f"{percentage:.2f}%"

def generate_pdf(invoice_data, output_path=None):
    """
    Modified to accept custom output path for web deployment
    If output_path is provided, saves to that location instead of default folder structure
    """
    if output_path:
        # For web deployment - save to specified temp file
        full_path = output_path
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
    else:
        # Original logic for desktop app
        place_of_supply = invoice_data['meta']['place_of_supply']
        customer_name = invoice_data['buyer']['name']
        
        # Sanitize folder names (remove invalid characters)
        sanitized_place = "".join(c for c in place_of_supply if c.isalnum() or c in (' ', '_', '-')).strip()
        sanitized_customer = "".join(c for c in customer_name if c.isalnum() or c in (' ', '_', '-')).strip()
        
        # Create nested folder structure
        place_folder = os.path.join(INVOICE_SAVE_PATH, sanitized_place)
        customer_folder = os.path.join(place_folder, sanitized_customer)
        os.makedirs(customer_folder, exist_ok=True)
        
        # Create filename: customername_date_invoiceno.pdf
        sanitized_date = invoice_data['meta']['date'].replace('/', '-')
        inv_no = invoice_data['meta']['no']
        filename = f"{sanitized_customer}_{sanitized_date}_{inv_no}.pdf"
        full_path = os.path.join(customer_folder, filename)
    
    # PDF generation code remains exactly the same
    c = canvas.Canvas(full_path, pagesize=A4)
    PAGE_W, PAGE_H = A4
    MARGIN_X = 15*mm
    MARGIN_Y = 15*mm
    INNER_W = PAGE_W - 2*MARGIN_X
    HALF_H = (PAGE_H - 2*MARGIN_Y)/2.0
    LINE_HEIGHT = 14
    SECTION_GAP = 12
    RUPEE = "Rs. "
    seller = {
        "name": "M/s Sukhrani Enterprises", 
        "addr": "63 B1 Charari Lal Bangla Kanpur, Uttar Pradesh", 
        "contact": "8604311514, GSTIN: 09AJBPA644Q2ZZ"
    }
    
    def money(v): 
        return f"{RUPEE}{v:,.2f}"
    
    def draw_line(c, x1, y, x2): 
        c.setLineWidth(0.6)
        c.line(x1, y, x2, y)
    
    def draw_header(c, x, y, copy_label):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x, y, seller["name"])
        c.setFont("Helvetica", 10)
        c.drawString(x, y-LINE_HEIGHT, seller["addr"])
        c.drawString(x, y-2*LINE_HEIGHT, seller["contact"])
        right = x+INNER_W
        c.setFont("Helvetica-Bold", 22)
        c.drawRightString(right, y, "INVOICE")
        c.setFont("Helvetica", 10)
        c.drawRightString(right, y-(LINE_HEIGHT*1.2), copy_label)
        draw_line(c, x, y-(LINE_HEIGHT*2.8), right)
        return y-(LINE_HEIGHT*2.8)-SECTION_GAP
    
    def draw_billing_meta(c, x, y):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, "Bill To:")
        buyer_y = y-LINE_HEIGHT*1.2
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, buyer_y, invoice_data['buyer']['name'])
        c.setFont("Helvetica", 10)
        c.drawString(x, buyer_y-LINE_HEIGHT, f"{invoice_data['buyer']['id_type']}: {invoice_data['buyer']['id_value']}")
        c.drawString(x, buyer_y-2*LINE_HEIGHT, f"Place of Supply: {invoice_data['meta']['place_of_supply']}")
        right = x+INNER_W
        c.drawRightString(right, y, f"Invoice #: {invoice_data['meta']['no']}")
        c.drawRightString(right, y-LINE_HEIGHT, f"Bill Date: {invoice_data['meta']['date']}")
        c.drawRightString(right, y-2*LINE_HEIGHT, f"Vehicle No: {invoice_data['meta']['vehicle_no']}")
        draw_line(c, x, buyer_y-(LINE_HEIGHT*2.8), right)
        return buyer_y-(LINE_HEIGHT*2.8)-SECTION_GAP
    
    def draw_items_table(c, x, y):
        COLS = [
            ("S.N.",0.05,"C"),("Items",0.25,"L"),("Qty.",0.06,"C"),("HSN",0.08,"C"),
            ("Rate",0.11,"R"),("Amount",0.13,"R"),("CGST",0.06,"C"),("SGST",0.06,"C"),
            ("Tax",0.12,"R"),("Total",0.14,"R")
        ]
        scale = 1.0/sum(w for _,w,_ in COLS)
        COLS = [(h, w*scale, a) for h,w,a in COLS]
        col_x = [x]
        for _, width_frac, _ in COLS: 
            col_x.append(col_x[-1] + INNER_W*width_frac)
        
        right = x+INNER_W
        table_top, HEADER_H, ROW_H = y, 18, 16
        c.setFillColorRGB(0.95,0.95,0.95)
        c.rect(x, table_top-HEADER_H, INNER_W, HEADER_H, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        
        for i, (label, _, align) in enumerate(COLS):
            if align=="L": 
                c.drawString(col_x[i]+5, table_top-12, label)
            elif align=="C": 
                c.drawCentredString((col_x[i]+col_x[i+1])/2, table_top-12, label)
            else: 
                c.drawRightString(col_x[i+1]-5, table_top-12, label)
        
        c.setFont("Helvetica", 9)
        current_y = table_top-HEADER_H
        
        for item in invoice_data['items']:
            current_y -= ROW_H
            cgst_display = format_tax_percentage(item['cgst'])
            sgst_display = format_tax_percentage(item['sgst'])
            
            data = [
                str(item['sn']), 
                item['name'], 
                str(item['qty']), 
                item['hsn'], 
                money(item['rate']), 
                money(item['amount']), 
                cgst_display,
                sgst_display,
                money(item['tax']),
                money(item['total'])
            ]
            
            for i, text in enumerate(data):
                align = COLS[i][2]
                if align=="L": 
                    c.drawString(col_x[i]+5, current_y+5, text)
                elif align=="C": 
                    c.drawCentredString((col_x[i]+col_x[i+1])/2, current_y+5, text)
                else: 
                    c.drawRightString(col_x[i+1]-5, current_y+5, text)
        
        table_bottom = current_y
        c.rect(x, table_bottom, INNER_W, table_top-table_bottom)
        c.line(x, table_top-HEADER_H, right, table_top-HEADER_H)
        
        for i in range(1, len(COLS)): 
            c.line(col_x[i], table_bottom, col_x[i], table_top)
        
        for i in range(len(invoice_data['items'])): 
            c.line(x, table_top-HEADER_H-(i*ROW_H), right, table_top-HEADER_H-(i*ROW_H))
        
        return table_bottom
    
    def draw_footer(c, x, y):
        right = x+INNER_W
        labels_x, values_x = right-180, right-5
        c.setFont("Helvetica", 11)
        c.drawString(labels_x, y-LINE_HEIGHT, "Total Amount")
        c.drawRightString(values_x, y-LINE_HEIGHT, money(invoice_data['totals']['amount']))
        c.drawString(labels_x, y-(LINE_HEIGHT*2), "Total Tax")
        c.drawRightString(values_x, y-(LINE_HEIGHT*2), money(invoice_data['totals']['tax']))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(labels_x, y-(LINE_HEIGHT*3), "GRAND TOTAL")
        c.drawRightString(values_x, y-(LINE_HEIGHT*3), money(invoice_data['totals']['grand_total']))
        draw_line(c, x, y-(LINE_HEIGHT*3.8), right)
        c.setFont("Helvetica", 10)
        c.drawString(x, y-(LINE_HEIGHT*4.8), "Make all checks payable to Sukhrani Enterprises")
        c.drawRightString(right, y-(LINE_HEIGHT*4.8), "Signature")
    
    def draw_invoice_copy(c, x, y_start, copy_label):
        y = draw_header(c, x, y_start, copy_label)
        y = draw_billing_meta(c, x, y)
        table_bottom = draw_items_table(c, x, y)
        draw_footer(c, x, table_bottom-SECTION_GAP)
    
    draw_invoice_copy(c, MARGIN_X, PAGE_H-MARGIN_Y, "Original Copy")
    mid_y = MARGIN_Y+HALF_H
    c.setDash(3, 2)
    c.line(MARGIN_X, mid_y, PAGE_W-MARGIN_X, mid_y)
    c.setDash()
    draw_invoice_copy(c, MARGIN_X, mid_y-30, "Duplicate Copy")
    
    c.showPage()
    c.save()
    print(f"\nInvoice generated successfully: {full_path}")
    
    # For web deployment, don't try to open the file automatically
    if not output_path:
        try:
            os.startfile(full_path)
        except Exception as e:
            print(f"Could not automatically open the PDF. Error: {e}")
    
    return full_path  # Return the path for web app to access the file