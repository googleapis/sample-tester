#!/bin/bash
cd $(dirname "${BASH_SOURCE[0]}")
SAMPLE_DIRECTORY=${SAMPLE_DIRECTORY:-../../../../../python-docs-samples/vision/cloud-client/product_search}

pushd ${SAMPLE_DIRECTORY} >& /dev/null
# echo "Calling list_products"
python3 ./product_management.py --project_id actools-sample-tester list_products "$@"
popd >& /dev/null
exit $?
