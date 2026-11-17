// The small surface of phylib.c that the browser needs. The physics itself is phylib.c, unchanged.
#include <stdlib.h>
#include "../../phylib.h"

// Ball positions are passed back to JavaScript as (number, x, y) triples in this buffer.
static double ballBuffer[PHYLIB_MAX_OBJECTS * 3];

double *ball_buffer(void) { return ballBuffer; }

phylib_table *table_new(void) { return phylib_new_table(); }

void table_free(phylib_table *table) { phylib_free_table(table); }

double table_time(phylib_table *table) { return table->time; }

void table_add_ball(phylib_table *table, int number, double x, double y)
{
    phylib_coord pos = phylib_new_coord(x, y);
    phylib_add_object(table, phylib_new_still_ball((unsigned char)number, &pos));
}

// Turns the cue ball into a rolling ball with the given velocity, with drag opposing it.
void table_shoot(phylib_table *table, double vx, double vy)
{
    for (int i = 0; i < PHYLIB_MAX_OBJECTS; i++)
    {
        phylib_object *ball = table->object[i];
        if (ball == NULL || ball->type != PHYLIB_STILL_BALL || ball->obj.still_ball.number != 0)
            continue;

        phylib_coord pos = ball->obj.still_ball.pos;
        phylib_coord vel = phylib_new_coord(vx, vy);
        phylib_coord acc = phylib_new_coord(0.0, 0.0);
        double speed = phylib_length(vel);
        if (speed > PHYLIB_VEL_EPSILON)
            acc = phylib_new_coord(-vx / speed * PHYLIB_DRAG, -vy / speed * PHYLIB_DRAG);

        table->object[i] = phylib_new_rolling_ball(0, &pos, &vel, &acc);
        free(ball);
        return;
    }
}

phylib_table *table_segment(phylib_table *table) { return phylib_segment(table); }

// Writes every ball's position after rolling for dt seconds into the buffer; returns the ball count.
int table_balls(phylib_table *table, double dt)
{
    int count = 0;
    for (int i = 0; i < PHYLIB_MAX_OBJECTS; i++)
    {
        phylib_object *ball = table->object[i];
        if (ball == NULL)
            continue;
        if (ball->type == PHYLIB_STILL_BALL)
        {
            ballBuffer[count * 3] = ball->obj.still_ball.number;
            ballBuffer[count * 3 + 1] = ball->obj.still_ball.pos.x;
            ballBuffer[count * 3 + 2] = ball->obj.still_ball.pos.y;
            count++;
        }
        else if (ball->type == PHYLIB_ROLLING_BALL)
        {
            phylib_object rolled = *ball;
            phylib_roll(&rolled, ball, dt);
            ballBuffer[count * 3] = rolled.obj.rolling_ball.number;
            ballBuffer[count * 3 + 1] = rolled.obj.rolling_ball.pos.x;
            ballBuffer[count * 3 + 2] = rolled.obj.rolling_ball.pos.y;
            count++;
        }
    }
    return count;
}
