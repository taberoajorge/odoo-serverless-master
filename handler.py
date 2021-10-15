import xmlrpc
import urllib.parse
from xmlrpc.client import ServerProxy
from settings import ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASS, TEAM_CHANELS


def process_contact(event, context):
    # print(event)
    print(event['body'])

    data_dict = urllib.parse.parse_qs(event['body'])
    
    print(data_dict)

    contact_name = '{} {}'.format(data_dict['contact_name'][0] , data_dict['contact_lastname'][0])    
    email_from = data_dict['contact_email'][0]
    x_nombre_comercial_crm = data_dict['e-name'][0]
   
    x_url = data_dict['url_from'][0]

    team_id = int([key for key, value in TEAM_CHANELS.items() 
    if data_dict['url_from'][0].find(value) != -1][0])

    user_id = 76 #int(data_dict['user_id'][0]) Pedro por defecto
    x_campo = data_dict['cant_suc'][0]
    
    try: #Campos opcionales
        phone = data_dict['contact_phone'][0]
    except KeyError:
        phone = 'No esta establecido'
    try: #Campos opcionales  
        description = data_dict['comments_box'][0]
    except KeyError:
        description = 'No esta establecido'

    request_data = {
        'stage_id': 1,
        'name': contact_name,
        'contact_name': contact_name,
        'phone': phone,
        'email_from': email_from,
        'x_nombre_comercial_crm': x_nombre_comercial_crm,
        'user_id': user_id,
        'team_id': team_id,
        'x_campo': x_campo,
        'description': description,
        'x_url': x_url,
        'tag_ids' : [100],
        'source_id' : 9,
        'type': 'opportunity',
    }

    with ServerProxy('{}/xmlrpc/common'.format(ODOO_URL)) as proxy:
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(ODOO_URL))                
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {}) 
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(ODOO_URL))

        # Validacion de email, retorna una lista con un solo elemento(id) siendo este el id de un usuario en el modelo de contactos
        email_validate = models.execute_kw(ODOO_DB, uid, ODOO_PASS, 'res.partner', 'search',[[['email', '=', request_data['email_from']]]])

        models.execute_kw(ODOO_DB, uid, ODOO_PASS, 'res.users', 'write', [[uid], {'company_id': 1}])

        # Si existe algun contacto con ese ID lo busca y lo indexa a la iniciativa
        if email_validate:

            final_data = {**request_data, **{'partner_id': email_validate[0]}}

        else:
        # Si no este crea un contacto y lo indexa a la iniciativa 
            partner_id = models.execute_kw(ODOO_DB, uid, ODOO_PASS, 'res.partner', 'create', [{
            'name': request_data['contact_name'],
            'email': request_data['email_from'],
            'phone': request_data['phone'],
        }])
            
            final_data = {**request_data, **{'partner_id': partner_id}}

        resp = models.execute_kw(ODOO_DB, uid, ODOO_PASS,'crm.lead', 'create', [final_data])
        
    return print(f'Se ha creado un iniciativa correctamente con el ID:{resp}')
