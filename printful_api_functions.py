'''
Copyright 2017, Florian Beutler

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

####################################################################

The functions here are used to communicate with the printful.com api
'''

from app import app
import json
import requests
import base64

def get_printful_variant_id(order):
    ''' 
    This function makes an api call to get all variants for a certain 
    product and than finds the variant id specified by the color and size 
    '''
    url = app.config['PRINTFUL_API_BASE'] + 'products/%d' % order.product.printful_product_id
    headers = {'content-type': 'application/json'}
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        print 'ERROR: get_printful_variant_id -- when retrieving list of variants with requests', e
        return False
    if response.status_code == 200:
        data = json.loads(response.text)
        # We count the number of positive variants we find, just to be sure that our variant 
        # selection is unique
        count = 0
        # Find the variant specified by the color and size of the order
        for variant in data['result']['variants']:
            # First we select the size (if size is not null). Size is null if the product comes in 
            # only one size
            if variant['size'] == 'null':
                # There is no case I know of were size and color are null
                if variant['color'] == order.color:
                    variant_id = variant['id']
                    count += 1
            elif variant['size'] == order.size:
                # Second we select the color (if color is not null). Color is null if 
                # the product comes in only one color
                if variant['color'] == 'null':
                    variant_id = variant['id']
                    count += 1
                elif variant['color'] == order.color:
                    variant_id = variant['id']
                    count += 1
        # to make absolutely sure that color and size define a variant for this product
        if count == 0:
            print 'ERROR: get_printful_variant_id -- no variant found with this size %s and color %s for product id %d' % (order.size, order.color, order.product.printful_product_id)
            return False
        elif count > 1:
            print 'ERROR: get_printful_variant_id -- size and color are not enough to define the variant for product id %d' % order.product.printful_product_id
            return False
        else:
            return variant_id
    else:
        print 'ERROR: get_printful_variant_id -- printfil api call unsuccessful, code = %d, message = %s' % (response.status_code, response.text)
        return False

def create_printful_order(order):
    ''' This function submits a printful order '''
    order_json = {
        "recipient": {
            "name": order.shipping_name,
            "address1": order.shipping_address,
            "city": order.shipping_city,
            "state_code": order.shipping_state_code,
            "country_code": order.shipping_country_code,
            "zip": order.shipping_zip_code
        },
        "items": [{}]
    }
    order_json['retail_costs'] = { "shipping": order.shipping_cost }
    items = []
    # Process each item in the order and attache them to the json object
    for order_item in order.items:
        item = {
            "variant_id": order_item.variant_id,
            "quantity": order_item.quantity,
            "name": order_item.product.title,
            "retail_price": order_item.product.price,
            "files": [{
                "id": order_item.print_file_id
            }]
        }
        items.append(item)
    order_json['items'] = items
    url = app.config['PRINTFUL_API_BASE'] + 'orders'
    b64Val = base64.b64encode(app.config['PRINTFUL_API_KEY'])
    headers = {'content-type': 'application/json', 'Authorization': "Basic %s" % b64Val}
    try:
        response = requests.post(url, data=json.dumps(order_json), headers=headers)
        print "response = ", response.status_code, response.text
        return True, response
    except requests.exceptions.RequestException as e:  
        print 'ERROR: create_printful_order -- when submitting order with requests, error message:', e
        return False, e
