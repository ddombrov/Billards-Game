#include "phylib.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

/**
 * This function will allocate memory for a new phylib_object,
 * set its type and transfer information.
 * It will return a pointer to the phylib_object or NULL
 */
phylib_object *phylib_new_still_ball(unsigned char number, phylib_coord *pos)
{

    phylib_object *object = malloc(sizeof(phylib_object));

    if (object == NULL)
    {
        return NULL;
    }
    if (pos == NULL)
    {
        free(object);
        return NULL;
    }
    object->type = PHYLIB_STILL_BALL;
    object->obj.still_ball.number = number;
    object->obj.still_ball.pos = *pos;
    return object;
}

/**
 * This function will allocate memory for a new phylib_object,
 * set its type and transfer information.
 * It will return a pointer to the phylib_object or NULL
 */
phylib_object *phylib_new_rolling_ball(unsigned char number,
                                       phylib_coord *pos,
                                       phylib_coord *vel,
                                       phylib_coord *acc)
{

    phylib_object *object = malloc(sizeof(phylib_object));

    if (object == NULL)
    {
        return NULL;
    }

    if (pos == NULL || vel == NULL || acc == NULL)
    {
        free(object);
        return NULL;
    }

    object->type = PHYLIB_ROLLING_BALL;
    object->obj.rolling_ball.number = number;
    object->obj.rolling_ball.pos = *pos;
    object->obj.rolling_ball.vel = *vel;
    object->obj.rolling_ball.acc = *acc;
    return object;
}

/**
 * This function will allocate memory for a new phylib_object,
 * set its type and transfer information.
 * It will return a pointer to the phylib_object or NULL
 */
phylib_object *phylib_new_hole(phylib_coord *pos)
{

    phylib_object *object = malloc(sizeof(phylib_object));

    if (object == NULL)
    {
        return NULL;
    }
    if (pos == NULL)
    {
        free(object);
        return NULL;
    }

    object->type = PHYLIB_HOLE;
    object->obj.hole.pos = *pos;
    return object;
}

/**
 * This function will allocate memory for a new phylib_object,
 * set its type and transfer information.
 * It will return a pointer to the phylib_object or NULL
 */
phylib_object *phylib_new_hcushion(double y)
{

    phylib_object *object = malloc(sizeof(phylib_object));

    if (object == NULL)
    {
        return NULL;
    }

    object->type = PHYLIB_HCUSHION;
    object->obj.hcushion.y = y;
    return object;
}

/**
 * This function will allocate memory for a new phylib_object,
 * set its type and transfer information.
 * It will return a pointer to the phylib_object or NULL
 */
phylib_object *phylib_new_vcushion(double x)
{

    phylib_object *object = malloc(sizeof(phylib_object));

    if (object == NULL)
    {
        return NULL;
    }

    object->type = PHYLIB_VCUSHION;
    object->obj.vcushion.x = x;
    return object;
}

/**
 * This function will allocate memory for a table. It will then assign the values of
 * its array elements to pointers to new objects created by the phylib_new_* functions.
 */
phylib_table *phylib_new_table(void)
{

    phylib_table *table = malloc(sizeof(phylib_table));

    if (table == NULL)
    {
        return NULL;
    }

    table->time = 0.0;

    // 1) a horizontal cushion at y=0.0;
    table->object[0] = phylib_new_hcushion(0.0);

    // 2) a horizontal cushion at y=PHYLIB_TABLE_LENGTH;
    table->object[1] = phylib_new_hcushion(PHYLIB_TABLE_LENGTH);

    // 3) a vertical cushion at x=0.0;
    table->object[2] = phylib_new_vcushion(0.0);

    // 4) a vertical cushion at x=PHYLIB_TABLE_WIDTH;
    table->object[3] = phylib_new_vcushion(PHYLIB_TABLE_WIDTH);

    // 5) 6 holes: positioned in the four corners where the cushions meet
    // and two more midway between the top holes and bottom holes.
    phylib_coord coord = phylib_new_coord(0.0, 0.0);
    table->object[4] = phylib_new_hole(&coord);
    phylib_coord coord2 = phylib_new_coord(0.0, PHYLIB_TABLE_LENGTH / 2);
    table->object[5] = phylib_new_hole(&coord2);
    phylib_coord coord3 = phylib_new_coord(0.0, PHYLIB_TABLE_LENGTH);
    table->object[6] = phylib_new_hole(&coord3);
    phylib_coord coord4 = phylib_new_coord(PHYLIB_TABLE_WIDTH, 0.0);
    table->object[7] = phylib_new_hole(&coord4);
    phylib_coord coord5 = phylib_new_coord(PHYLIB_TABLE_WIDTH, PHYLIB_TABLE_LENGTH / 2);
    table->object[8] = phylib_new_hole(&coord5);
    phylib_coord coord6 = phylib_new_coord(PHYLIB_TABLE_WIDTH, PHYLIB_TABLE_LENGTH);
    table->object[9] = phylib_new_hole(&coord6);

    // The remaining pointers will all be set to NULL
    for (int i = 10; i < PHYLIB_MAX_OBJECTS; i++)
    {
        table->object[i] = NULL;
    }

    return table;
}

/**
 * This function will allocate memory for a new phylib_coord and transfer the information
 * provided in the function parameters into the structure. It will return a phylib_coord.
 */
phylib_coord phylib_new_coord(double x, double y)
{
    phylib_coord coord;
    coord.x = x;
    coord.y = y;
    return coord;
}

/**
 * This function should allocate new memory for a phylib_object. Save the address of that
 * object at the location pointed to by dest, and copy over the contents of the object from the
 * location pointed to by src.
 */
void phylib_copy_object(phylib_object **dest, phylib_object **src)
{

    if (dest == NULL)
    {
        return;
    }

    if (src == NULL || *src == NULL)
    {
        *dest = NULL;
        return;
    }

    *dest = malloc(sizeof(phylib_object));
    if (*dest != NULL)
    {
        memcpy(*dest, *src, sizeof(phylib_object));
    }
    return;
}

/**
 * This function should allocate memory for a new phylib_table, returning NULL if the malloc
 * fails. Then the contents pointed to by table should be copied to the new memory location and
 * the address returned.
 */
phylib_table *phylib_copy_table(phylib_table *table)
{

    if (table == NULL)
    {
        return NULL;
    }

    phylib_table *copiedTable = malloc(sizeof(phylib_table));

    if (copiedTable == NULL)
    {
        return NULL;
    }

    copiedTable->time = table->time;

    for (int i = 0; i < PHYLIB_MAX_OBJECTS; ++i)
    {
        phylib_copy_object(&(copiedTable->object[i]), &(table->object[i]));
    }

    return copiedTable;
}

/**
 * This function should iterate over the object array in the table until it finds a NULL pointer. It
 * should then assign that pointer to be equal to the address of object. If there are no NULL
 * pointers in the array, the function should do nothing.
 */
void phylib_add_object(phylib_table *table, phylib_object *object)
{

    for (int i = 0; i < PHYLIB_MAX_OBJECTS; i++)
    {
        if (table->object[i] == NULL)
        {
            table->object[i] = object;
            break;
        }
    }
    return;
}

/**
 * This function should free every non- NULL pointer in the object array of table. It should then
 * also free table as well.
 */
void phylib_free_table(phylib_table *table)
{
    for (int i = 0; i < PHYLIB_MAX_OBJECTS; i++)
    {
        free(table->object[i]);
        table->object[i] = NULL;
    }
    free(table);
    return;
}

/**
 * This function should return the difference between c1 and c2. That is the result’s x value
 * should be c1.x-c2.x and similarly for y.
 */
phylib_coord phylib_sub(phylib_coord c1, phylib_coord c2)
{
    phylib_coord coord;
    coord.x = c1.x - c2.x;
    coord.y = c1.y - c2.y;
    return coord;
}

/**
 * This function should return the length of the vector/coordinate c. You can calculate this length
 * by using Pythagorean theorem.
 */
double phylib_length(phylib_coord c)
{
    if (c.x * c.x + c.y * c.y >= 0)
    {
        return sqrt(c.x * c.x + c.y * c.y);
    }
    return 0;
}

/**
 * This function should compute the dot-product between two vectors. Hint: the dot product is
 * equal to the sum of: the product of the x-values and the product of the y-values.
 */
double phylib_dot_product(phylib_coord a, phylib_coord b)
{
    return a.x * b.x + a.y * b.y;
}

/**
 * This function should calculate the distance between two objects, obj1 and obj2. obj1 must be
 * a PHYLIB_ROLLING_BALL.
 */
double phylib_distance(phylib_object *obj1, phylib_object *obj2)
{

    if (obj1->type != PHYLIB_ROLLING_BALL)
    {
        return -1.0;
    }

    double distance;
    phylib_coord coord;

    switch (obj2->type)
    {

        // 1) If obj2 is another BALL ( ROLLING or STILL), then compute the distance between the
        // centres of the two balls and subtract two radii (i.e. one PHYLIB_BALL_DIAMETER)
    case PHYLIB_STILL_BALL:
        coord = phylib_sub(obj1->obj.rolling_ball.pos, obj2->obj.still_ball.pos);
        distance = phylib_length(coord);
        distance -= PHYLIB_BALL_DIAMETER;
        break;
    case PHYLIB_ROLLING_BALL:
        coord = phylib_sub(obj1->obj.rolling_ball.pos, obj2->obj.rolling_ball.pos);
        distance = phylib_length(coord);
        distance -= PHYLIB_BALL_DIAMETER;
        break;

        // 2) If obj2 is a HOLE, then compute the distance between the centre of the ball and the
        // hole and subtract the HOLE_RADIUS.
    case PHYLIB_HOLE:
        coord = phylib_sub(obj1->obj.rolling_ball.pos, obj2->obj.hole.pos);
        distance = phylib_length(coord);
        distance -= PHYLIB_HOLE_RADIUS;
        break;

        // If obj2 is a CUSHION calculate the distance between the centre of the ball and the
        // CUSION and subtract the BALL_RADIUS. Hint: use fabs since the ball might be left/above
        // or right/below to CUSHION.
    case PHYLIB_HCUSHION:
        
        distance = fabs(obj1->obj.rolling_ball.pos.y-obj2->obj.hcushion.y);
        distance -= PHYLIB_BALL_RADIUS;
        break;
    case PHYLIB_VCUSHION:
 
        distance = fabs(obj1->obj.rolling_ball.pos.x-obj2->obj.vcushion.x);
        distance -= PHYLIB_BALL_RADIUS;
        break;

    default:
        return -1.0;
    }
    return distance;
}

/**
 * This function updates a new phylib_object that represents the old phylib_object after it
 * has rolled for a period of time
 */
void phylib_roll(phylib_object *new, phylib_object *old, double time)
{

    // If new and old are not PHYLIB_ROLLING_BALLs, then the function should do nothing.
    if (new->type == PHYLIB_ROLLING_BALL && old->type == PHYLIB_ROLLING_BALL)
    {

        // p = p1 + v1t + (1/2)(a1t^2)
        new->obj.rolling_ball.pos.x = old->obj.rolling_ball.pos.x + old->obj.rolling_ball.vel.x *time +
                                      0.5 * old->obj.rolling_ball.acc.x *time *time;
        new->obj.rolling_ball.pos.y = old->obj.rolling_ball.pos.y + old->obj.rolling_ball.vel.y *time +
                                      0.5 * old->obj.rolling_ball.acc.y *time *time;

        // v = v1 + a1t
        new->obj.rolling_ball.vel.x = old->obj.rolling_ball.vel.x + old->obj.rolling_ball.acc.x *time;
        new->obj.rolling_ball.vel.y = old->obj.rolling_ball.vel.y + old->obj.rolling_ball.acc.y *time;

        // If either velocity changes sign, then that velocity and its corresponding acc
        //( x, or y) must be set to zero (if both vel.s change sign,
        // then both vel.s and both acc.s must be set to zero).
        if ((old->obj.rolling_ball.vel.x < 0) != (new->obj.rolling_ball.vel.x < 0))
        {
            new->obj.rolling_ball.vel.x = 0;
            new->obj.rolling_ball.acc.x = 0;
        }
        if ((old->obj.rolling_ball.vel.y < 0) != (new->obj.rolling_ball.vel.y < 0))
        {
            new->obj.rolling_ball.vel.y = 0;
            new->obj.rolling_ball.acc.y = 0;
        }
    }

    return;
}

/**
 * This function will check whether a ROLLING_BALL has stopped, and if it has, will convert it to a
 * STILL_BALL. You may assume that object is a ROLLING_BALL.
 */
unsigned char phylib_stopped(phylib_object *object)
{

    if (object == NULL)
    {
        return 0;
    }

    // For the purposes of this simulation a ball is considered to have stopped if its speed
    // (which is the length of its velocity) is less than PHYLIB_VEL_EPSILON.
    if (phylib_length(object->obj.rolling_ball.vel) < PHYLIB_VEL_EPSILON)
    {

        // Do not assume that the number, and x and y positions of the rolling ball will be automatically
        // transferred to the still ball.
        object->type = PHYLIB_STILL_BALL;
        object->obj.still_ball.number = object->obj.rolling_ball.number;
        object->obj.still_ball.pos = object->obj.rolling_ball.pos;
        return 1;
    }

    return 0;
}

/**
 * This is the most complicated function in the assignment but it can be handled by divide and
 * conquer based on the type of object b. You may assume that object a is a ROLLING_BALL.
 * Note that the two arguments to this function are double pointers. That is, they are pointers to
 * pointers to phylib_objectss.
 */
void phylib_bounce(phylib_object **a, phylib_object **b)
{

    phylib_coord r_ab;

    switch ((*b)->type)
    {

        // In this case the y velocity and y acceleration of a are reversed (negated). This is the
        // physical principle of angle of incidence equals angle of reflection.
    case PHYLIB_HCUSHION:
        (*a)->obj.rolling_ball.vel.y = -1 * (*a)->obj.rolling_ball.vel.y;
        (*a)->obj.rolling_ball.acc.y = -1 * (*a)->obj.rolling_ball.acc.y;
        break;

        // In this case the x velocity and x acceleration of a are reversed (negated). This is the
        // physical principle of angle of incidence equals angle of reflection.
    case PHYLIB_VCUSHION:
        (*a)->obj.rolling_ball.vel.x = -1 * (*a)->obj.rolling_ball.vel.x;
        (*a)->obj.rolling_ball.acc.x = -1 * (*a)->obj.rolling_ball.acc.x;
        break;

        // In this case, free the memory of a and set it to NULL. This represents the ball falling off
        // the table.
    case PHYLIB_HOLE:
        free(*a);
        *a = NULL;
        break;

        // In this case, “upgrade” the STILL_BALL to a ROLLING BALL and proceed directly to CASE
        // 5 (do not collect $200). HINT: if you leave out the break statement at the end of a case
        // condition, the code will continue with the next case.
    case PHYLIB_STILL_BALL:
        (*b)->type = PHYLIB_ROLLING_BALL;
        (*b)->obj.rolling_ball.vel.x = 0;
        (*b)->obj.rolling_ball.vel.y = 0;
        (*b)->obj.rolling_ball.acc.x = 0;
        (*b)->obj.rolling_ball.acc.y = 0;
        (*b)->obj.rolling_ball.number = (*b)->obj.still_ball.number;
        (*b)->obj.rolling_ball.pos = (*b)->obj.still_ball.pos;

        // This one is a little bit tricky and will require us to calculate a few intermediate values
        // before we can know the speeds and directions of the two balls after they collide.
    case PHYLIB_ROLLING_BALL:

        // Compute the position of a with respect to b: subtract the position of b from a
        r_ab = phylib_sub((*a)->obj.rolling_ball.pos, (*b)->obj.rolling_ball.pos);

        // Compute the relative velocity of a with respect to b: subtract the velocity of b from a
        phylib_coord v_rel = phylib_sub((*a)->obj.rolling_ball.vel, (*b)->obj.rolling_ball.vel);

        // Divide the x and y components of r_ab by the length of r_ab
        double nx = r_ab.x / phylib_length(r_ab);
        double ny = r_ab.y / phylib_length(r_ab);
        phylib_coord n = phylib_new_coord(nx, ny);

        // Calculate the ratio of the relative velocity, v_rel, in the direction of ball a by computing
        // the dot_product of v_rel with respect to n
        double v_rel_n = phylib_dot_product(v_rel, n);

        // Update the x (and then y) velocity of ball a by subtracting v_rel_n multipied by the x (and then y) component of
        // vector n
        (*a)->obj.rolling_ball.vel.x -= v_rel_n * n.x;
        (*a)->obj.rolling_ball.vel.y -= v_rel_n * n.y;

        // Update the x and y velocities of ball b by adding the product of v_rel_n and vector n.
        (*b)->obj.rolling_ball.vel.x += v_rel_n * n.x;
        (*b)->obj.rolling_ball.vel.y += v_rel_n * n.y;

        // Compute the speed of a and b as the lengths of their velocities
        double speedA = phylib_length((*a)->obj.rolling_ball.vel);
        double speedB = phylib_length((*b)->obj.rolling_ball.vel);

        if (speedA > PHYLIB_VEL_EPSILON)
        {
            (*a)->obj.rolling_ball.acc.x = (-1 * ((*a)->obj.rolling_ball.vel.x) / speedA) * PHYLIB_DRAG;
            (*a)->obj.rolling_ball.acc.y = (-1 * ((*a)->obj.rolling_ball.vel.y) / speedA) * PHYLIB_DRAG;
        }

        if (speedB > PHYLIB_VEL_EPSILON)
        {
            (*b)->obj.rolling_ball.acc.x = (-1 * ((*b)->obj.rolling_ball.vel.x) / speedB) * PHYLIB_DRAG;
            (*b)->obj.rolling_ball.acc.y = (-1 * ((*b)->obj.rolling_ball.vel.y) / speedB) * PHYLIB_DRAG;
        }
        break;
    default:
        return;
    }
    return;
}

/**
 * This function should return the number of ROLLING_BALLS on the table.
 */
unsigned char phylib_rolling(phylib_table *t)
{
    int rollingBallCount = 0;
    if (t != NULL)
    {
        for (int i = 0; i < PHYLIB_MAX_OBJECTS; i++)
        {
            if (t->object[i] != NULL && t->object[i]->type == PHYLIB_ROLLING_BALL)
            {
                rollingBallCount++;
            }
        }
    }

    return rollingBallCount;
}

/**
 * This function should return a segment of a pool shot, as follows.
 */
phylib_table *phylib_segment(phylib_table *table)
{

    if (phylib_rolling(table) == 0)
    {
        return NULL;
    }

    phylib_table *copiedTable = phylib_copy_table(table);

    // The loop over the time should end if: 1) PHYLIB_MAX_TIME is reached
    double time = PHYLIB_SIM_RATE;
    
    while (time <= PHYLIB_MAX_TIME) 
            {
                time += PHYLIB_SIM_RATE;

        for (int i = 0; i < PHYLIB_MAX_OBJECTS; i++)
        {

            if (copiedTable->object[i] != NULL && copiedTable->object[i]->type == PHYLIB_ROLLING_BALL)
            {

                phylib_roll(copiedTable->object[i], table->object[i], time);
            }
        }

        for (int i = 0; i < PHYLIB_MAX_OBJECTS; i++)
        {

            if (copiedTable->object[i] != NULL && copiedTable->object[i]->type == PHYLIB_ROLLING_BALL)
            {

                // 3) A ROLLING_BALL has stopped.
                if (phylib_stopped(copiedTable->object[i]))
                {
                    copiedTable->time=table->time+time;
                    return copiedTable;
                }
                for (int j = 0; j < PHYLIB_MAX_OBJECTS; j++)
                {
                    if (j != i)
                    {

                        phylib_object *obj2 = copiedTable->object[j];

                        if (obj2 != NULL)
                        {
                            // 2) The phylib_distance between the ball and another phylib_object is less than 0.0.
                            if (phylib_distance(copiedTable->object[i], obj2) < 0.0)
                            {
                                copiedTable->time=table->time+time;
                                phylib_bounce(&(copiedTable->object[i]), &obj2);
                                return copiedTable;
                            }
                            // printf("\n\n\n%lf\n%lf\n",time,phylib_distance(copiedTable->object[i], obj2));
                        }
                    }
                }
            }
        }
        
    }
    return copiedTable;
}

char *phylib_object_string(phylib_object *object)
{
    static char string[80];
    if (object == NULL)
    {
        snprintf(string, 80, "NULL;");
        return string;
    }
    switch (object->type)
    {
    case PHYLIB_STILL_BALL:
        snprintf(string, 80,
                 "STILL_BALL (%d,%6.1lf,%6.1lf)",
                 object->obj.still_ball.number,
                 object->obj.still_ball.pos.x,
                 object->obj.still_ball.pos.y);
        break;
    case PHYLIB_ROLLING_BALL:
        snprintf(string, 80,
                 "ROLLING_BALL (%d,%6.1lf,%6.1lf,%6.1lf,%6.1lf,%6.1lf,%6.1lf)",
                 object->obj.rolling_ball.number,
                 object->obj.rolling_ball.pos.x,
                 object->obj.rolling_ball.pos.y,
                 object->obj.rolling_ball.vel.x,
                 object->obj.rolling_ball.vel.y,
                 object->obj.rolling_ball.acc.x,
                 object->obj.rolling_ball.acc.y);
        break;
    case PHYLIB_HOLE:
        snprintf(string, 80,
                 "HOLE (%6.1lf,%6.1lf)",
                 object->obj.hole.pos.x,
                 object->obj.hole.pos.y);
        break;
    case PHYLIB_HCUSHION:
        snprintf(string, 80,
                 "HCUSHION (%6.1lf)",
                 object->obj.hcushion.y);
        break;
    case PHYLIB_VCUSHION:
        snprintf(string, 80,
                 "VCUSHION (%6.1lf)",
                 object->obj.vcushion.x);
        break;
    }
    return string;
}
