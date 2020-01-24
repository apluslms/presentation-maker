#!/bin/bash

if [ "$1" == 'no-xvfb' ]
then
    shift
    presentation_maker "$@"
else
    # xvfb (virtual window system) is needed for deck2pdf.
    xvfb-run -s '-screen 0 640x480x24' presentation_maker "$@"
fi

