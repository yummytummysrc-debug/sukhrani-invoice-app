import streamlit as st
import pandas as pd
import json
import datetime
import tempfile
import os

# Import your existing backend
import invoice_app as backend

# Configure Streamlit
st.set_page_config(
    page_title="Sukhrani Enterprises Invoice System",
    page_icon="📄",
    layout="wide"
)

def load_existing_data():
    """Load data from your existing JSON files"""
    try:
        # Try to load from your existing JSON files
        sku_data = backend.load_data('sku_data.json', backend.DEFAULT_SKU_DATA)
        customer_data = backend.load_data('customer_data.json', backend.DEFAULT_CUSTOMER_DATA)
        vehicle_data = backend.load_data('vehicle_data.json', backend.DEFAULT_VEHICLE_DATA)
        
        return sku_data, customer_data, vehicle_data.get("vehicles", [])
    except:
        # Fallback to defaults if files don't exist
        return backend.DEFAULT_SKU_DATA, backend.DEFAULT_CUSTOMER_DATA, backend.DEFAULT_VEHICLE_DATA.get("vehicles", [])

def initialize_session_data():
    """Initialize data in session state from existing files"""
    if 'data_loaded' not in st.session_state:
        sku_data, customer_data, vehicle_list = load_existing_data()
        
        st.session_state.sku_data = sku_data
        st.session_state.customer_data = customer_data  
        st.session_state.vehicle_list = vehicle_list
        st.session_state.data_loaded = True

def save_data_to_files():
    """Save current session data back to JSON files"""
    try:
        backend.save_data('sku_data.json', st.session_state.sku_data)
        backend.save_data('customer_data.json', st.session_state.customer_data)
        backend.save_data('vehicle_data.json', {"vehicles": st.session_state.vehicle_list})
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

def main():
    # Initialize data from existing files
    initialize_session_data()
    
    # Header
    st.title("Sukhrani Enterprises Invoice System")
    st.markdown("*Created By - Prashant Agrahari*")
    st.caption("⚡ Using existing JSON data files")
    
    # Data management sidebar
    with st.sidebar:
        st.subheader("Data Management")
        
        if st.button("💾 Save to Files"):
            if save_data_to_files():
                st.success("Data saved to JSON files!")
            
        if st.button("🔄 Reload from Files"):
            st.session_state.data_loaded = False
            st.rerun()
        
        # Export data
        if st.button("📥 Download Backup"):
            export_data = {
                "sku_data": st.session_state.sku_data,
                "customer_data": st.session_state.customer_data,
                "vehicle_data": {"vehicles": st.session_state.vehicle_list},
                "export_date": datetime.datetime.now().isoformat()
            }
            
            filename = f"sukhrani_backup_{datetime.date.today().strftime('%Y%m%d')}.json"
            st.download_button(
                label="📥 Download JSON Backup",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=filename,
                mime="application/json"
            )
    
    # Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Operation:", [
        "Generate Invoice",
        "Manage Customers", 
        "Manage SKUs",
        "Manage Vehicles",
        "Dashboard"
    ])
    
    # Generate Invoice Page
    if page == "Generate Invoice":
        st.header("📝 Generate New Invoice")
        
        # Basic details
        col1, col2 = st.columns(2)
        
        with col1:
            invoice_no = st.number_input("Invoice Number", min_value=1, value=101)
            
        with col2:
            if st.session_state.vehicle_list:
                vehicle_no = st.selectbox("Vehicle Number", st.session_state.vehicle_list)
            else:
                vehicle_no = st.text_input("Vehicle Number", placeholder="e.g., UP78 JT 9555")
        
        # Customer selection
        places = list(st.session_state.customer_data.keys())
        if places:
            col1, col2 = st.columns(2)
            with col1:
                place_of_supply = st.selectbox("Place of Supply", places)
            with col2:
                customers = [c['name'] for c in st.session_state.customer_data[place_of_supply]]
                if customers:
                    customer_name = st.selectbox("Customer", customers)
                else:
                    st.error(f"No customers found in {place_of_supply}")
                    st.stop()
        else:
            st.error("No customers found. Please add customers first.")
            st.stop()
        
        st.subheader("Add Items")
        
        # Item addition
        with st.form("add_item_form", clear_on_submit=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                items = list(st.session_state.sku_data.keys())
                if items:
                    selected_item = st.selectbox("Item", items)
                else:
                    st.error("No SKUs found. Please add SKUs first.")
                    st.stop()
            
            with col2:
                weights = st.session_state.sku_data[selected_item].get("weights", [])
                if weights and any(w.strip() for w in weights):
                    selected_weight = st.selectbox("Weight", weights)
                else:
                    selected_weight = st.text_input("Weight", placeholder="Enter weight")
            
            with col3:
                quantity = st.number_input("Quantity", min_value=1, value=1)
            
            with col4:
                rate = st.number_input("Rate (₹)", min_value=0.0, value=0.0, format="%.2f")
            
            add_item = st.form_submit_button("Add Item")
        
        # Initialize invoice items
        if 'invoice_items' not in st.session_state:
            st.session_state.invoice_items = []
        
        if add_item and rate > 0:
            item_name = f"{selected_item} ({selected_weight})" if selected_weight else selected_item
            item_details = st.session_state.sku_data[selected_item]
            amount = rate * quantity
            tax = amount * (item_details['cgst'] + item_details['sgst'])
            
            new_item = {
                'sn': len(st.session_state.invoice_items) + 1,
                'name': item_name,
                'qty': quantity,
                'hsn': item_details['hsn'],
                'rate': rate,
                'amount': amount,
                'cgst': item_details['cgst'],
                'sgst': item_details['sgst'],
                'tax': tax,
                'total': amount + tax
            }
            
            st.session_state.invoice_items.append(new_item)
            st.success("Item added!")
        
        # Display current items
        if st.session_state.invoice_items:
            st.subheader("Invoice Items")
            
            # Display as table
            df_display = []
            for item in st.session_state.invoice_items:
                df_display.append({
                    'S.N.': item['sn'],
                    'Item': item['name'],
                    'Qty': item['qty'],
                    'Rate (₹)': f"{item['rate']:.2f}",
                    'Amount (₹)': f"{item['amount']:.2f}",
                    'Tax (₹)': f"{item['tax']:.2f}",
                    'Total (₹)': f"{item['total']:.2f}"
                })
            
            st.dataframe(pd.DataFrame(df_display), use_container_width=True)
            
            # Remove item
            col1, col2 = st.columns(2)
            with col1:
                if st.session_state.invoice_items:
                    item_options = [f"{i+1}. {item['name']}" for i, item in enumerate(st.session_state.invoice_items)]
                    item_to_remove = st.selectbox("Select item to remove", [""] + item_options)
            
            with col2:
                if st.button("Remove Item") and item_to_remove:
                    index = int(item_to_remove.split(".")[0]) - 1
                    st.session_state.invoice_items.pop(index)
                    # Reindex
                    for i, item in enumerate(st.session_state.invoice_items):
                        item['sn'] = i + 1
                    st.rerun()
            
            # Generate invoice
            if st.button("🔄 Generate PDF Invoice", type="primary"):
                try:
                    # Get customer details
                    customer_obj = next(c for c in st.session_state.customer_data[place_of_supply] 
                                      if c['name'] == customer_name)
                    
                    # Calculate totals
                    adjusted_items, final_totals, _ = backend.apply_price_adjustments(st.session_state.invoice_items)
                    
                    # Prepare invoice data
                    invoice_data = {
                        "meta": {
                            "no": invoice_no,
                            "date": datetime.date.today().strftime("%d/%m/%Y"),
                            "place_of_supply": place_of_supply,
                            "vehicle_no": vehicle_no
                        },
                        "buyer": customer_obj,
                        "items": adjusted_items,
                        "totals": final_totals
                    }
                    
                    # Generate PDF
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                        pdf_path = backend.generate_pdf(invoice_data, tmp.name)
                        
                        # Read PDF
                        with open(tmp.name, 'rb') as pdf_file:
                            pdf_bytes = pdf_file.read()
                        
                        # Offer download
                        filename = f"invoice_{invoice_no}_{datetime.date.today().strftime('%Y%m%d')}.pdf"
                        st.download_button(
                            label="📥 Download Invoice PDF",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf"
                        )
                        
                        st.success(f"Invoice #{invoice_no} generated successfully!")
                        
                        # Display totals
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Amount", f"₹{final_totals['amount']:.2f}")
                        with col2:
                            st.metric("Total Tax", f"₹{final_totals['tax']:.2f}")
                        with col3:
                            st.metric("Grand Total", f"₹{final_totals['grand_total']:.2f}")
                        
                        # Clear items
                        if st.button("🗑️ Clear Invoice Items"):
                            st.session_state.invoice_items = []
                            st.rerun()
                        
                        # Cleanup
                        os.unlink(tmp.name)
                        
                except Exception as e:
                    st.error(f"Error generating invoice: {str(e)}")
    
    # Manage Customers Page
    elif page == "Manage Customers":
        st.header("👥 Manage Customers")
        
        tab1, tab2, tab3 = st.tabs(["Add Customer", "View Customers", "Edit Customer"])
        
        with tab1:
            st.subheader("Add New Customer")
            with st.form("add_customer"):
                col1, col2 = st.columns(2)
                
                with col1:
                    customer_name = st.text_input("Customer Name")
                    place_of_supply = st.text_input("Place of Supply")
                
                with col2:
                    id_type = st.selectbox("ID Type", ["GSTN", "AADHAR"])
                    id_value = st.text_input("ID Number")
                
                if st.form_submit_button("Add Customer"):
                    if all([customer_name, place_of_supply, id_value]):
                        new_customer = {
                            "name": customer_name,
                            "id_type": id_type,
                            "id_value": id_value.upper()
                        }
                        
                        if place_of_supply.title() not in st.session_state.customer_data:
                            st.session_state.customer_data[place_of_supply.title()] = []
                        
                        st.session_state.customer_data[place_of_supply.title()].append(new_customer)
                        st.success(f"Customer '{customer_name}' added successfully!")
                    else:
                        st.error("All fields are required")
        
        with tab2:
            st.subheader("All Customers")
            total_customers = sum(len(customers) for customers in st.session_state.customer_data.values())
            st.info(f"Total customers: {total_customers}")
            
            for place, customers in st.session_state.customer_data.items():
                with st.expander(f"📍 {place} ({len(customers)} customers)"):
                    for i, customer in enumerate(customers):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{customer['name']}**")
                            st.write(f"   {customer['id_type']}: {customer['id_value']}")
                        with col2:
                            if st.button(f"Delete", key=f"del_{place}_{i}"):
                                st.session_state.customer_data[place].pop(i)
                                st.rerun()
        
        with tab3:
            st.subheader("Edit Customer")
            
            # Select customer to edit
            places = list(st.session_state.customer_data.keys())
            if places:
                selected_place = st.selectbox("Select Place", places, key="edit_place")
                customers = st.session_state.customer_data[selected_place]
                
                if customers:
                    customer_names = [f"{i}: {c['name']}" for i, c in enumerate(customers)]
                    selected_customer_idx = st.selectbox("Select Customer", customer_names, key="edit_customer")
                    
                    if selected_customer_idx:
                        idx = int(selected_customer_idx.split(":")[0])
                        customer = customers[idx]
                        
                        with st.form("edit_customer_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                new_name = st.text_input("Customer Name", value=customer['name'])
                                new_place = st.text_input("Place of Supply", value=selected_place)
                            
                            with col2:
                                new_id_type = st.selectbox("ID Type", ["GSTN", "AADHAR"], 
                                                         index=0 if customer['id_type'] == 'GSTN' else 1)
                                new_id_value = st.text_input("ID Number", value=customer['id_value'])
                            
                            if st.form_submit_button("Update Customer"):
                                if all([new_name, new_place, new_id_value]):
                                    # Remove from old location
                                    st.session_state.customer_data[selected_place].pop(idx)
                                    if not st.session_state.customer_data[selected_place]:
                                        del st.session_state.customer_data[selected_place]
                                    
                                    # Add to new location
                                    updated_customer = {
                                        "name": new_name,
                                        "id_type": new_id_type,
                                        "id_value": new_id_value.upper()
                                    }
                                    
                                    if new_place not in st.session_state.customer_data:
                                        st.session_state.customer_data[new_place] = []
                                    
                                    st.session_state.customer_data[new_place].append(updated_customer)
                                    st.success("Customer updated successfully!")
                                    st.rerun()
                                else:
                                    st.error("All fields are required")
                else:
                    st.info("No customers in selected place")
            else:
                st.info("No customers found")
    
    # Manage SKUs Page
    elif page == "Manage SKUs":
        st.header("📦 Manage SKUs")
        
        tab1, tab2, tab3 = st.tabs(["Add SKU", "View SKUs", "Edit SKU"])
        
        with tab1:
            st.subheader("Add New SKU")
            with st.form("add_sku"):
                col1, col2 = st.columns(2)
                
                with col1:
                    item_name = st.text_input("Item Name")
                    hsn_code = st.text_input("HSN Code")
                
                with col2:
                    cgst_rate = st.number_input("CGST Rate (e.g., 0.025 for 2.5%)", min_value=0.0, max_value=1.0, format="%.3f")
                    sgst_rate = st.number_input("SGST Rate (e.g., 0.025 for 2.5%)", min_value=0.0, max_value=1.0, format="%.3f")
                
                weights_input = st.text_input("Weights (comma-separated)", placeholder="1 L, 500 mL, 250 mL")
                
                if st.form_submit_button("Add SKU"):
                    if all([item_name, hsn_code]):
                        weights = [w.strip() for w in weights_input.split(',') if w.strip()] if weights_input else []
                        
                        new_sku = {
                            "hsn": hsn_code,
                            "cgst": cgst_rate,
                            "sgst": sgst_rate,
                            "weights": weights
                        }
                        
                        st.session_state.sku_data[item_name.title()] = new_sku
                        st.success(f"SKU '{item_name}' added successfully!")
                    else:
                        st.error("Item name and HSN code are required")
        
        with tab2:
            st.subheader("All SKUs")
            st.info(f"Total SKUs: {len(st.session_state.sku_data)}")
            
            for item_name, sku_data in st.session_state.sku_data.items():
                with st.expander(f"📦 {item_name}"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.write(f"**HSN:** {sku_data['hsn']}")
                        st.write(f"**CGST:** {sku_data['cgst']*100}%")
                    
                    with col2:
                        st.write(f"**SGST:** {sku_data['sgst']*100}%")
                        st.write(f"**Total Tax:** {(sku_data['cgst']+sku_data['sgst'])*100}%")
                    
                    with col3:
                        if sku_data['weights']:
                            st.write(f"**Weights:** {', '.join(sku_data['weights'])}")
                        else:
                            st.write("**Weights:** N/A")
                    
                    with col4:
                        if st.button(f"Delete SKU", key=f"del_sku_{item_name}"):
                            del st.session_state.sku_data[item_name]
                            st.rerun()
        
        with tab3:
            st.subheader("Edit SKU")
            
            sku_names = list(st.session_state.sku_data.keys())
            if sku_names:
                selected_sku = st.selectbox("Select SKU to Edit", sku_names, key="edit_sku_select")
                
                if selected_sku:
                    sku_data = st.session_state.sku_data[selected_sku]
                    
                    with st.form("edit_sku_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_name = st.text_input("Item Name", value=selected_sku)
                            new_hsn = st.text_input("HSN Code", value=sku_data['hsn'])
                        
                        with col2:
                            new_cgst = st.number_input("CGST Rate", value=sku_data['cgst'], format="%.3f")
                            new_sgst = st.number_input("SGST Rate", value=sku_data['sgst'], format="%.3f")
                        
                        current_weights = ', '.join(sku_data['weights']) if sku_data['weights'] else ''
                        new_weights_str = st.text_input("Weights (comma-separated)", value=current_weights)
                        
                        if st.form_submit_button("Update SKU"):
                            if all([new_name, new_hsn]):
                                new_weights = [w.strip() for w in new_weights_str.split(',') if w.strip()] if new_weights_str else []
                                
                                updated_sku = {
                                    "hsn": new_hsn,
                                    "cgst": new_cgst,
                                    "sgst": new_sgst,
                                    "weights": new_weights
                                }
                                
                                # Remove old entry if name changed
                                if selected_sku != new_name:
                                    del st.session_state.sku_data[selected_sku]
                                
                                st.session_state.sku_data[new_name] = updated_sku
                                st.success("SKU updated successfully!")
                                st.rerun()
                            else:
                                st.error("Item name and HSN code are required")
            else:
                st.info("No SKUs found")
    
    # Manage Vehicles Page
    elif page == "Manage Vehicles":
        st.header("🚛 Manage Vehicles")
        
        tab1, tab2, tab3 = st.tabs(["Add Vehicle", "View Vehicles", "Edit Vehicle"])
        
        with tab1:
            st.subheader("Add New Vehicle")
            with st.form("add_vehicle"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    code = st.text_input("Code (e.g., UP78)")
                
                with col2:
                    series = st.text_input("Series (e.g., JT)")
                
                with col3:
                    number = st.text_input("Number (e.g., 9555)")
                
                if st.form_submit_button("Add Vehicle"):
                    if all([code, series, number]):
                        vehicle_number = f"{code.upper()} {series.upper()} {number}"
                        
                        if vehicle_number not in st.session_state.vehicle_list:
                            st.session_state.vehicle_list.append(vehicle_number)
                            st.success(f"Vehicle '{vehicle_number}' added successfully!")
                        else:
                            st.error("Vehicle already exists")
                    else:
                        st.error("All fields are required")
        
        with tab2:
            st.subheader("All Vehicles")
            st.info(f"Total vehicles: {len(st.session_state.vehicle_list)}")
            
            for i, vehicle in enumerate(st.session_state.vehicle_list):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"🚛 {vehicle}")
                with col2:
                    if st.button("Delete", key=f"del_vehicle_{i}"):
                        st.session_state.vehicle_list.pop(i)
                        st.rerun()
        
        with tab3:
            st.subheader("Edit Vehicle")
            
            if st.session_state.vehicle_list:
                vehicle_options = [f"{i}: {v}" for i, v in enumerate(st.session_state.vehicle_list)]
                selected_vehicle_idx = st.selectbox("Select Vehicle to Edit", vehicle_options, key="edit_vehicle_select")
                
                if selected_vehicle_idx:
                    idx = int(selected_vehicle_idx.split(":")[0])
                    current_vehicle = st.session_state.vehicle_list[idx]
                    
                    # Parse current vehicle
                    parts = current_vehicle.split()
                    current_code = parts[0] if len(parts) > 0 else ""
                    current_series = parts[1] if len(parts) > 1 else ""
                    current_number = " ".join(parts[2:]) if len(parts) > 2 else ""
                    
                    with st.form("edit_vehicle_form"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            new_code = st.text_input("Code", value=current_code)
                        
                        with col2:
                            new_series = st.text_input("Series", value=current_series)
                        
                        with col3:
                            new_number = st.text_input("Number", value=current_number)
                        
                        if st.form_submit_button("Update Vehicle"):
                            if all([new_code, new_series, new_number]):
                                new_vehicle = f"{new_code.upper()} {new_series.upper()} {new_number}"
                                st.session_state.vehicle_list[idx] = new_vehicle
                                st.success("Vehicle updated successfully!")
                                st.rerun()
                            else:
                                st.error("All fields are required")
            else:
                st.info("No vehicles found")
    
    # Dashboard
    elif page == "Dashboard":
        st.header("📊 Dashboard")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total SKUs", len(st.session_state.sku_data))
        
        with col2:
            total_customers = sum(len(customers) for customers in st.session_state.customer_data.values())
            st.metric("Total Customers", total_customers)
        
        with col3:
            st.metric("Total Vehicles", len(st.session_state.vehicle_list))
        
        # Display data summary
        st.subheader("Data Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Customers by Location:**")
            for place, customers in st.session_state.customer_data.items():
                st.write(f"• {place}: {len(customers)} customers")
        
        with col2:
            st.write("**Recent SKUs:**")
            for i, (name, data) in enumerate(list(st.session_state.sku_data.items())[:5]):
                st.write(f"• {name} (HSN: {data['hsn']})")
        
        st.info("💡 Remember to click 'Save to Files' to persist your changes to JSON files!")

if __name__ == "__main__":
    main()