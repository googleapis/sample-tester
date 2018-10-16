#!/bin/bash
cd $(dirname "${BASH_SOURCE[0]}")
SAMPLE_DIRECTORY=${SAMPLE_DIRECTORY:-../../../../../python-docs-samples/vision/cloud-client/product_search}

pushd ${SAMPLE_DIRECTORY} >& /dev/null
# echo "Calling delete_product"
python3 ./product_management.py --project_id actools-sample-tester delete_product "$@"
popd >& /dev/null
exit $?
