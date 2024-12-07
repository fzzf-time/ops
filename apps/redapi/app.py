import logging

from flask import Flask, jsonify


app = Flask(__name__)
from libs.db import pg


@app.route('/queries/<string:qname>', methods=['GET'])
def queries(qname):
    logging.info(f"query name: {qname}")

    redash = pg(app.config['redash_dsn'])
    queries = redash.query("select query from queries where name=%s and 'redapi'=any(tags)", (qname,))
    if not queries:
        return jsonify({"error": "query not found"}), 404
    
    query = queries[0][0]
    db = pg(app.config['db_dsn'])
    result = db.query(query, as_dict=True)
    return jsonify(result), 200


def redapi(db_dsn, redash_dsn):
    app.config['db_dsn'] = db_dsn
    app.config['redash_dsn'] = redash_dsn
    app.run(host='0.0.0.0', port=80)