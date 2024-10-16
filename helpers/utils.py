from .decorators import *
from django.core.paginator import Paginator,EmptyPage, PageNotAnInteger
from rest_framework.pagination import PageNumberPagination
import uuid
import base64


def get_rand_number(number_of_digit):
    return str(int(str(uuid.uuid4().int)[:number_of_digit]))



class CustomPagination(PageNumberPagination):
    
    def __init__(self, default_page_size):
        self.page_size= default_page_size  # default page size

        self.page_size_query_param = 'page_size' # query parameter to specify page size
        self.max_page_size = 100 # maximum allowed page size

    def get_previous_page_number(self):
        if self.page.has_previous():
            return self.page.previous_page_number()

    def get_next_page_number(self):
        if self.page.has_next():
            return self.page.next_page_number()

    def pagination_meta_data(self):
        return {
            'page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'total_items': self.page.paginator.count,
            'next_page': self.get_next_page_number(),
            'previous_page': self.get_previous_page_number(),
        }
    

def serilalizer_error_list(serilaizer_error):
    error_list = []
    for field, errors in serilaizer_error.items():
        for error in errors:
            error_list.append(f'{field}: {error}')
    
    return error_list




def paginate(request, data_list, items_per_page):
    paginator = Paginator(data_list, items_per_page)
    page = request.GET.get('page')

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return {
        'items': page_obj,
        'page_obj': page_obj,
        'paginator': paginator
    }


def dict_filter(data_dict, filters):
    result = {}
    for key, value in data_dict.items():
        if key in filters:
            result[key] = value
    return result


def generate_unique_id(digit):
    return str(int(str(uuid.uuid4().int)[:digit]))


def encoding_string(string_data):
    encoded_bytes = base64.b64encode(string_data.encode('utf-8'))
    encoded_string = encoded_bytes.decode('utf-8')
    return encoded_string

def decode_string(encoded_string):
    decoded_bytes = base64.b64decode(encoded_string)
    decoded_string = decoded_bytes.decode('utf-8')
    return decoded_string