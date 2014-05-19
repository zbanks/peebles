#include <stdio.h>
#include <math.h>

int rate;
int chunksize;

typedef struct
{
	char active;
	int note;
	float velocity;
	float t;
	float hit;
	float release;
} note_t;

float reduce(float cur,float new)
{
	return cur+new;
}

float f(float t)
{
	if(fmod(t,1)<0.5)
	{
		return -1;
	}
	return 1;
}

float gen(note_t* note)
{
	float freq=pow(2,(note->note-69)/12.)*440.;
	float base;
	base=f(freq*note->t)*note->velocity;
	return base;
}

char still_active(note_t* note)
{
	if(note->release > note->hit && (note->t - note->hit) > 0)
	{
		return 0;
	}
	return 1;
}

void synth(float* buffer,note_t* notes,int num_notes)
{
	int i,j;
	float delta_t=1./rate;

	for(j=0;j<chunksize;j++)
	{
		buffer[j]=0;
	}

	for(i=0;i<num_notes;i++)
	{
		if(!notes[i].active)
		{
			continue;
		}

		for(j=0;j<chunksize;j++)
		{
			buffer[j]=reduce(buffer[j],gen(&(notes[i])));
			notes[i].t+=delta_t;
		}

		notes[i].active=still_active(&(notes[i]));
	}
}

int main()
{
	rate=48000;
	chunksize=2048;

	note_t note[2];

	float buffer[chunksize];

	int i;

	note[0].active=1;
	note[0].note=69;
	note[0].velocity=.1;
	note[0].t=0;
	note[0].hit=0;
	note[0].release=-1;

	note[1].active=1;
	note[1].note=72;
	note[1].velocity=.1;
	note[1].t=0;
	note[1].hit=0;
	note[1].release=-1;

	synth(buffer,note,2);

	for(i=0;i<chunksize;i++)
	{
		printf("%f, ",buffer[i]);
	}
	printf("\n");
}
