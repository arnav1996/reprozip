#!/bin/sh

case "$TEST_MODE"
in
    run_program)
        (while read line; do echo "$line"; sh -c "$line" || exit $?; done)<<'EOF'
        reprozip testrun bash -c "cat ../../../../../etc/passwd;cd /var/lib;cat ../../etc/group"
        reprozip trace bash -c "cat /etc/passwd;echo"
        reprozip trace --continue sh -c "cat /etc/group;/usr/bin/id"
        reprozip graph graph.dot
        reprozip pack
EOF
        ;;
    check_style)
        flake8 --ignore=E126 reprozip
        ;;
esac