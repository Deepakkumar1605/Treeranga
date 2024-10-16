function get_order_detail(element){
    
    var uid = element.getAttribute('uid');
    var url = '/orders/admin_order_details/'+uid;

    document.getElementById('order_number').innerHTML = uid;

    axios.get(url)
    .then(function (response) {
        var res_data = response.data;
        console.log(response.data);

        var html1='\
        <p>Order Amount : <span>'+res_data.order_value+'</span></p>\
        <p>Transaction-ID : <span>'+res_data.transaction_id+'</span></p>\
        <p>Payment Status : <span>'+res_data.payment_status+'</span></p>\
        <p>Order Status : <span>'+res_data.order_status+'</span></p>\
        <p>Delivary Charge : <span>'+res_data.coupon+'</span></p>\
        <p>Coupon : <span>'+res_data.coupon+'</span></p>\
        <p>Address : <span>'+res_data.address+'</span></p>\
        '
        document.getElementById('order_details_data').innerHTML = html1;

        // product list 
        var target = document.getElementById('product_list');
        target.innerHTML='';

        for(var pro =0; pro < response.data.products.length; pro++){
            var data = response.data.products[pro];

            var html= '\
            <tr>\
                <th scope="row">'+pro+'</th>\
                <td>'+data['product']['uid']+'</td>\
                <td>'+data['quantity']+'</td>\
                <td>'+data['product']['brand']+'</td>\
            </tr>\
            '
            target.innerHTML+=html;
        }


        var myModal = new bootstrap.Modal(document.getElementById('order_details'));
        myModal.show();
    })
}

