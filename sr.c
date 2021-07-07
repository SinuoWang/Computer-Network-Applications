#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include "emulator.h"
#include "sr.h"

/* ******************************************************************
   Go Back N protocol.  Adapted from
   ALTERNATING BIT AND GO-BACK-N NETWORK EMULATOR: VERSION 1.1  J.F.Kurose

   Network properties:
   - one way network delay averages five time units (longer if there
   are other messages in the channel for GBN), but can be larger
   - packets can be corrupted (either the header or the data portion)
   or lost, according to user-defined probabilities
   - packets will be delivered in the order in which they were sent
   (although some can be lost).

   Modifications (6/6/2008 - CLP):
   - removed bidirectional GBN code and other code not used by prac.
   - fixed C style to adhere to current programming style
   (24/3/2013 - CLP)
   - added GBN implementation
**********************************************************************/

#define RTT  15.0       /* round trip time.  MUST BE SET TO 15.0 when submitting assignment */
#define WINDOWSIZE 6    /* Maximum number of buffered unacked packet */
#define SEQSPACE 12      /* SR sequence number must be at least twice the window size */
#define NOTINUSE (-1)   /* used to fill header fields that are not being used */

/* generic procedure to compute the checksum of a packet.  Used by both sender and receiver
   the simulator will overwrite part of your packet with 'z's.  It will not overwrite your
   original checksum.  This procedure must generate a different checksum to the original if
   the packet is corrupted.
*/
int ComputeChecksum(struct pkt packet)
{
  int checksum = 0;
  int i;

  checksum = packet.seqnum;
  checksum += packet.acknum;
  for ( i=0; i<20; i++ )
    checksum += (int)(packet.payload[i]);

  return checksum;
}

bool IsCorrupted(struct pkt packet)
{
  if (packet.checksum == ComputeChecksum(packet))
    return (false);
  else
    return (true);
}


/********* Sender (A) variables and functions ************/

static struct pkt buffer[WINDOWSIZE];  /* array for storing packets waiting for ACK */
static int windowfirst, windowlast;    /* array indexes of the first/last packet awaiting ACK */
static int windowcount;                /* the number of packets currently awaiting an ACK */
static int A_nextseqnum;               /* the next sequence number to be used by the sender */

/* called from layer 5 (application layer), passed the message to be sent to other side */
void A_output(struct msg message)
{
  struct pkt sendpkt;
  int i;

  /* if not blocked waiting on ACK */
  if ( windowcount < WINDOWSIZE) {
    if (TRACE > 1)
      printf("----A: New message arrives, send window is not full, send new messge to layer3!\n");

    /* create packet */
    sendpkt.seqnum = A_nextseqnum;
    sendpkt.acknum = NOTINUSE;


    for ( i=0; i<20 ; i++ )
      sendpkt.payload[i] = message.data[i];
    sendpkt.checksum = ComputeChecksum(sendpkt);

    /* put packet in window buffer */
    /* windowlast will always be 0 for alternating bit; but not for GoBackN */
    windowlast = (windowlast + 1) % WINDOWSIZE;
    buffer[windowlast] = sendpkt;
    windowcount++;

    /* send out packet */
    if (TRACE > 0)
      printf("Sending packet %d to layer 3\n", sendpkt.seqnum);
    tolayer3 (A, sendpkt);


    /* start timer if first packet in window */
    if (windowcount == 1)
      starttimer(A,RTT);



    /* get next sequence number, wrap back to 0 */
    A_nextseqnum = (A_nextseqnum + 1) % SEQSPACE;
  }
  /* if blocked,  window is full */
  else {
    if (TRACE > 0)
      printf("----A: New message arrives, send window is full\n");
    window_full++;
  }
}


/* called from layer 3, when a packet arrives for layer 4
   In this practical this will always be an ACK as B never sends data.
*/
void A_input(struct pkt packet)
{
  int ackcount = 0;
  int i;


  /* if received ACK is not corrupted */
  if (!IsCorrupted(packet)) {
    if (TRACE > 0)
      printf("----A: uncorrupted ACK %d is received\n",packet.acknum);
    total_ACKs_received++;

    /* check if new ACK or duplicate */
    if (windowcount != 0) {
          int seqfirst = buffer[windowfirst].seqnum;
          int seqlast = buffer[windowlast].seqnum;
          /* check case when seqnum has and hasn't wrapped */
          if (((seqfirst <= seqlast) && (packet.acknum >= seqfirst && packet.acknum <= seqlast)) ||
              ((seqfirst > seqlast) && (packet.acknum >= seqfirst || packet.acknum <= seqlast))) {

            /* packet is a new ACK */
            if (TRACE > 0)
              printf("----A: ACK %d is not a duplicate\n",packet.acknum);
            new_ACKs++;


              /*correctly reveived the ACK*/

              for(i=0; i<WINDOWSIZE; i++)
              {
                 if(buffer[i].seqnum == packet.acknum)
                 {

                   buffer[i].acknum = 5;
                   break;
                 }
              }

              if(seqfirst==packet.acknum){
              /* shift the window while correctly acked*/
               while(buffer[windowfirst].acknum != -1 && windowcount!=0){
                  /* slide window by the number of packets ACKed */
                  windowfirst = (windowfirst + 1) % WINDOWSIZE;
                  /* delete the acked packets from window buffer */
                  windowcount--;
                }
                  /* start timer again if there are still more unacked packets in window */
                  stoptimer(A);
                  if (windowcount > 0)
                    starttimer(A, RTT);
                  }
              }
              /*seqnum wrapped i.e. duplicate */
              else
                if (TRACE > 0)
              printf ("----A: duplicate ACK received, do nothing!\n");
          }
  }
  /*corrupted*/
  else
    if (TRACE > 0)
      printf ("----A: corrupted ACK is received, do nothing!\n");
}

/* called when A's timer goes off */
void A_timerinterrupt(void)
{
  int i=0;

  if (TRACE > 0)
    printf("----A: time out,resend packets!\n");

  for(i=0; i<WINDOWSIZE; i++) {
    if(buffer[(windowfirst+i)%WINDOWSIZE].acknum == -1){ /*if did not receive the ack before the timeout*/
                              /*  then resend*/
      if (TRACE > 0)
        printf ("---A: resending packet %d\n", (buffer[(windowfirst+i) % WINDOWSIZE]).seqnum);

      tolayer3(A,buffer[(windowfirst+i) % WINDOWSIZE]);
      packets_resent++;
      starttimer(A,RTT);
      break;
    }
  }
}



/* the following routine will be called once (only) before any other */
/* entity A routines are called. You can use it to do any initialization */
void A_init(void)
{
  /* initialise A's window, buffer and sequence number */
  A_nextseqnum = 0;  /* A starts with seq num 0, do not change this */
  windowfirst = 0;
  windowlast = -1;   /* windowlast is where the last packet sent is stored.
         new packets are placed in winlast + 1
         so initially this is set to -1
       */
  windowcount = 0;
}



/********* Receiver (B)  variables and procedures ************/

static int expectedseqnum; /* the sequence number expected next by the receiver */
static int B_nextseqnum;   /* the sequence number for the next packets sent by B */
static int B_windowfirst; /* the window size in GBN is 1, but there is window_full in the receiver side in SR, */
static int B_windowlast;
static int B_windowend;
static int B_windowcount;
static struct pkt B_buffer[WINDOWSIZE];


/* called from layer 3, when a packet arrives for layer 4 at B*/
void B_input(struct pkt packet)
{
  struct pkt sendpkt;
  int i;
  B_windowend= (B_windowfirst+WINDOWSIZE-1)%SEQSPACE;
  if(!IsCorrupted(packet)){
    packets_received++;
    if (TRACE > 0)
      printf("----B: packet %d is correctly received, send ACK!\n",packet.seqnum);


    /* inside the window*/
    if(((B_windowfirst>B_windowend)&&((packet.seqnum>=B_windowfirst)&&(packet.seqnum<=11) ||((packet.seqnum>=0)&&(packet.seqnum<=B_windowend)) )) ||
        (B_windowfirst<B_windowend)&&(packet.seqnum>=B_windowfirst)&&(packet.seqnum<=B_windowend) ) {


        /*if it's a new one i.e. haven't been acked before*/
        if(packet.acknum == -1){
          int idx = packet.seqnum-B_windowfirst;
          B_buffer[idx]=packet;
          B_buffer[idx].acknum=packet.seqnum;
          B_buffer[idx].seqnum=packet.seqnum;
          B_windowcount++;
        }
        /* send an ACK for the received packet */
        sendpkt.acknum = packet.seqnum;


            /* we don't have any data to send.  fill payload with 0's */
            for ( i=0; i<20 ; i++ )
              sendpkt.payload[i] = '0';

            /* computer checksum */
            sendpkt.checksum = ComputeChecksum(sendpkt);

            /* send out packet */
            tolayer3 (B, sendpkt);

            int j=0;
            int k=0;
                for( j=0; j<WINDOWSIZE; j++)
                {
                  if(B_buffer[0].acknum != -1){
                  /* deliver to receiving application */
                  tolayer5(B, B_buffer[0].payload);
                  /*shift the pkt in window while the window shift*/
                    for( k=0; k<WINDOWSIZE-1;k++){
                      B_buffer[k]=B_buffer[k+1];
                    }
                    B_buffer[5].acknum=-1;
                    /*update the variables*/
                    B_windowfirst = (B_windowfirst+1) % SEQSPACE;
                    B_windowlast = (B_windowlast + 1) % SEQSPACE;
                    B_windowend = (B_windowend+1)%SEQSPACE;
                    B_windowcount--;
                }
                else
                {
                  break;
                }
              }


    }

    /* else not in the window, i.e. before the window */
    else{
      sendpkt.acknum = packet.seqnum;

          /* we don't have any data to send.  fill payload with 0's */
          for ( i=0; i<20 ; i++ )
            sendpkt.payload[i] = '0';

          /* computer checksum */
          sendpkt.checksum = ComputeChecksum(sendpkt);

          /* send out packet */
          tolayer3 (B, sendpkt);

    }





    }

   
  }



/* the following routine will be called once (only) before any other */
/* entity B routines are called. You can use it to do any initialization */
void B_init(void)
{
  /* initialise B's window, buffer and sequence number */
  B_nextseqnum = 1;
  expectedseqnum = 0;

  /* We need window in B side in SR*/
  B_windowfirst = 0;
  B_windowlast = -1;   /* windowlast is where the last packet sent is stored.
         new packets are placed in winlast + 1
         so initially this is set to -1
       */
  B_windowcount = 0;
  int i;
  for(i=0; i<WINDOWSIZE; i++)
  {
    B_buffer[i].acknum = -1;
  }
}

/******************************************************************************
 * The following functions need be completed only for bi-directional messages *
 *****************************************************************************/

/* Note that with simplex transfer from a-to-B, there is no B_output() */
void B_output(struct msg message)
{
}

/* called when B's timer goes off */
void B_timerinterrupt(void)
{
  /* unidirectional, does not required to be filled*/
}
