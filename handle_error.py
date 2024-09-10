from flask import jsonify

def handle_error(e):
    """
    Maneja los errores y genera una respuesta adecuada en formato JSON.
    """
    print(f"Error manejado: {str(e)}")
    return jsonify({
        'status': 'error',
        'message': str(e)
    }), 500
