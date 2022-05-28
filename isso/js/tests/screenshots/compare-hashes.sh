#!/bin/bash

# This script takes the output of the screenshot puppeteer test and compares
# the generated images against hashes of known-to-be-good images.
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Please only check in hashes rendered through the docker environment as
# otherwise you'll be dependent on aliasing and font rendering settings on your
# OS!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# Requirements:
# - imagemagick (for "identify" program)
# - bash        (hopefully this script should run on any shell though)

SCREENSHOTS_PATH=isso/js/tests/screenshots/reference
update=false

for i in "$@"; do
  case $i in
    -u)
      update=true
      shift # past argument=value
      ;;
    -*)
      echo "Unknown option $i"
      exit 1
      ;;
    *)
      ;;
  esac
done

echo "Computing screenshot hashes..."

comment_hash=$(/usr/bin/identify -quiet -format "%#" $SCREENSHOTS_PATH/comment.png) || exit 1
postbox_hash=$(/usr/bin/identify -quiet -format "%#" $SCREENSHOTS_PATH/postbox.png) || exit 1
thread_hash=$(/usr/bin/identify -quiet -format "%#" $SCREENSHOTS_PATH/thread.png) || exit 1

if [ $update = "true" ]; then
    echo "Updating screenshot hashes..."
    echo "$comment_hash" > $SCREENSHOTS_PATH/comment.png.hash
    echo "$postbox_hash" > $SCREENSHOTS_PATH/postbox.png.hash
    echo "$thread_hash" > $SCREENSHOTS_PATH/thread.png.hash
    echo ""
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo "Please only check in hashes rendered through the docker environment as"
    echo "otherwise you'll be dependent on aliasing and font rendering settings on your"
    echo "OS!"
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    exit 0
fi

echo "Comparing hashes against reference images..."

read -r expected_comment < $SCREENSHOTS_PATH/comment.png.hash
read -r expected_postbox < $SCREENSHOTS_PATH/postbox.png.hash
read -r expected_thread < $SCREENSHOTS_PATH/thread.png.hash

failed=false

if [ $comment_hash != $expected_comment ]; then
    echo "Screenshot hash does not match for comment!"
    echo "Expected hash:        $expected_comment"
    echo "Computed (new) hash:  $comment_hash"
    failed=true
fi
if [ $postbox_hash != $expected_postbox ]; then
    echo "Screenshot hash does not match for postbox!"
    echo "Expected hash:        $expected_postbox"
    echo "Computed (new) hash:  $postbox_hash"
    failed=true
fi
if [ $thread_hash != $expected_thread ]; then
    echo "Screenshot hash does not match for thread!"
    echo "Expected hash:        $expected_thread"
    echo "Computed (new) hash:  $thread_hash"
    failed=true
fi

if [ $failed = "true" ]; then
    echo ""
    echo "*** ERROR: *** One or more screenshots do not match (see above)."
    echo ""
    echo "To update screenshot hashes, run this script with the '-u' flag"
    echo "You can do this e.g. via Docker. Run:"
    echo "$ make docker"
    echo "$ docker-compose up -d"
    echo "$ make docker-update-screenshots"
    echo ""
    exit 1
else
    echo "Everything fine, screenshots have not changed."
fi
